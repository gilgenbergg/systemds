from pyspark import SparkContext

from slicing.base.top_k import Topk
from slicing.sparked import sparked_utils
from slicing.sparked.sparked_slicer import flatten
from slicing.sparked.sparked_utils import update_top_k


def update_nodes(partial_res, nodes_list, cur_lvl_res, w):
    for item in partial_res:
        if item.key not in cur_lvl_res:
            cur_lvl_res[item.key] = item
            nodes_list.append(item)
        else:
            cur_lvl_res[item.key].update_bounds(item.s_upper, item.s_lower, item.e_upper, item.e_max_upper, w)
    return cur_lvl_res, nodes_list



def process(all_features, predictions, f_l2, sc, debug, alpha, k, w, loss_type, enumerator):
    top_k = Topk(k)
    cur_lvl = 0
    levels = []
    all_features = list(all_features)
    first_tasks = sc.parallelize(all_features)
    partitions = first_tasks.glom()
    SparkContext.broadcast(sc, top_k)
    first_level = partitions.map(lambda features: sparked_utils.make_first_level(features, predictions, f_l2, top_k,
                                                                                 alpha, k, w, loss_type))
    first_lvl_res = first_level.reduce(lambda a, b: a + b)
    update_top_k(first_lvl_res, top_k, alpha, predictions)
    SparkContext.broadcast(sc, top_k)
    levels.append(first_lvl_res)
    levels.append(first_lvl_res)
    SparkContext.broadcast(sc, levels)
    cur_lvl = 2
    top_k.print_topk()
    SparkContext.broadcast(sc, top_k)
    while len(levels[cur_lvl - 1]) > 0:
        cur_lvl_res = {}
        nodes_list = []
        for left in range(int(cur_lvl / 2)):
            right = cur_lvl - 1 - left
            partitions = sc.parallelize(levels[left])
            part = partitions.glom()
            print(levels[right])
            mapped = part.map(lambda nodes: sparked_utils.nodes_enum(nodes, levels[right], predictions, f_l2,
                                                                      top_k, alpha, k, w, loss_type, cur_lvl, debug, enumerator))
            partial_nodes = mapped.reduce(lambda a, b: a + b)
            partial_res = flatten(partial_nodes)
            result = update_nodes(partial_res, nodes_list, cur_lvl_res, w)
            cur_lvl_res = result[0]
            nodes_list = result[1]
        levels.append(nodes_list)
        SparkContext.broadcast(sc, levels)
        SparkContext.broadcast(sc, top_k)
        update_top_k(list(nodes_list), top_k, alpha, predictions)
        SparkContext.broadcast(sc, top_k)
        cur_lvl = cur_lvl + 1
        top_k.print_topk()
        print("Level " + str(cur_lvl) + " had " + str(len(levels) * (len(levels) - 1)) +
              " candidates but after pruning only " + str(len(cur_lvl_res)) + " go to the next level")
    print("Program stopped at level " + str(cur_lvl))
    print()
    print("Selected slices are: ")
    top_k.print_topk()


