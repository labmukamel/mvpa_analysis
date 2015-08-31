#!/bin/bash

set -u
set -e
date
sub="$(zeropad $1 3)"
nperm=$2
flavor=$3
dir=${DATA_DIR}/LP/mvpa
ds_dir=${dir}/ds/${flavor}
res_dir=${dir}/results/${flavor}
mkdir -p ${dir}/results/${flavor}
for iter in `seq 0 $nperm`;
        do
	if [ "$iter" = "0" ]; then
		pymvpa2 searchlight \
			-i ${ds_dir}/sub${sub}_14_hrf.hdf5 \
			--payload pymvpa2_cv_setup.py \
			--neighbors 2 \
			--cv-balance-training 'equal' \
			--scatter-rois 2 \
			--nproc 40\
			-o ${res_dir}/sub${sub}_14_hrf_sl_orig.hdf5
			
		pymvpa2 searchlight \
			-i ${ds_dir}/sub${sub}_23_hrf.hdf5 \
			--payload pymvpa2_cv_setup.py \
			--neighbors 2 \
			--cv-balance-training 'equal' \
			--scatter-rois 2 \
			--nproc 40\
			-o ${res_dir}/sub${sub}_23_hrf_sl_orig.hdf5
	else
		iter="$(zeropad $iter 3)"
		echo $iter
		pymvpa2 searchlight \
			-i ${ds_dir}/sub${sub}_14_hrf.hdf5 \
			--payload pymvpa2_cv_setup.py \
			--neighbors 2 \
			--cv-balance-training 'equal' \
			--scatter-rois 2 \
			--nproc 40\
			-o ${res_dir}/sub${sub}_14_hrf_sl_perm${iter}.hdf5
		# save some space: we only need the samples
			pymvpa2 dump \
				-i ${res_dir}/sub${sub}_14_hrf_sl_perm${iter}.hdf5 \
				-o ${res_dir}/sub${sub}_14_hrf_sl_perm${iter}.npy \
				-f npy \
				-s
		

		pymvpa2 searchlight \
			-i ${ds_dir}/sub${sub}_23_hrf.hdf5 \
			--payload pymvpa2_cv_setup.py \
			--neighbors 2 \
			--cv-balance-training 'equal' \
			--scatter-rois 2 \
			--nproc 40\
			-o ${res_dir}/sub${sub}_23_hrf_sl_perm${iter}.hdf5
		# save some space: we only need the samples
			pymvpa2 dump \
				-i ${res_dir}/sub${sub}_23_hrf_sl_perm${iter}.hdf5 \
				-o ${res_dir}/sub${sub}_23_hrf_sl_perm${iter}.npy \
				-f npy \
				-s
		rm ${res_dir}/sub${sub}_14_hrf_sl_perm${iter}.hdf5
		rm ${res_dir}/sub${sub}_23_hrf_sl_perm${iter}.hdf5
	fi
done 
date;
