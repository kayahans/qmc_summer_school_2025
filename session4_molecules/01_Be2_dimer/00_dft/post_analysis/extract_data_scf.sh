#/bin/bash/

echo "#Method          HF                 LDA                 PBE                PBE0             SCAN" > scf_energy_summary.dat
for j in cc-pvdz cc-pvtz cc-pvqz 
do 
	echo -n "$j" >> scf_energy_summary.dat
	for i in HF LDA PBE PBE0 SCAN
	do  
		y=$(grep "converged SCF energy =" runs/Be2/$j/$i/scf/scf.out | sed s/"converged SCF energy ="/""/g) 
		echo -n "$y  " >> scf_energy_summary.dat 
	done
	echo " 0" >> scf_energy_summary.dat
done 
