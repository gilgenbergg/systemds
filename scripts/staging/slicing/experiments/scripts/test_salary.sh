#!/bin/bash

rm ~/slicing/experiments/archive/v1/resSalary

source ~/slicing/venv/bin/activate 

touch ~/slicing/experiments/archive/v1/resSalary
echo -e "alpha \t k \t\t w \t \t Time_taken" > ~/slicing/experiments/archive/v1/resSalary

k=10
debug=False
lossType=0
bUpdate=True

for j in {1..4}
do
		alpha=$[2**$j]
		echo "alpha = $alpha"
		echo "-----------------------------"
		for i in `seq 0 0.1 1` 
	do 
		w=$i
			echo "w = $w"
			echo "-----------------------------"
			start=$(date +%s%N)
			cd /home/lana/diploma/project
			python -m slicing.tests.regression.test_salary $k $w $alpha $bUpdate $debug $lossType
			end=$(date +%s%N)
			echo -e $alpha '\t\t' $k '\t' $w '\t' $((($end-$start)/1000000)) >> ~/slicing/experiments/archive/v1/resSalary
	done
done
#done