#!/usr/local/bin/python3

"""Train the model"""

import argparse
import logging
import os,sys
import pdb

import tensorflow as tf
from tqdm import tqdm
from src.graph import ModelGraph
from src.utils import Params

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('params', help="Path to params.json file containing different hyperparameters")
    parser.add_argument('mode', help="Indicate which model to train. Options: train_text2mel, train_ssrn")
    parser.add_argument('--gpu', type=int, default=0,help="GPU to train on if multiple available")
    args = parser.parse_args()

    params = Params(args.params)
    print('Running a training run with params from: {}'.format(args.params))
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)  # default use single GPU
    g = ModelGraph(params,args.mode)
    logger = g.logger
    sv = tf.train.Supervisor(logdir=params.log_dir, save_model_secs=0, global_step=g.global_step)
    with sv.managed_session() as sess:
        while True:
            for _ in tqdm(range(g.num_batch), total=g.num_batch, ncols=70, leave=False, unit='b'):
                # sess = tf_debug.LocalCLIDebugWrapperSession(sess)
                _, global_step, loss_out, L1_out, CE_out = sess.run([g.train_op, g.global_step,
                                                                            g.loss, g.L1_loss, g.CE_loss])
    
                if global_step % 50==0:
                    logger.info('Training loss at step {}: {:.4f}, L1: {:.4f}, CE: {:.4f}'.format(
                        global_step,loss_out, L1_out, CE_out))
    
                # Write checkpoint files at every 1k steps
                if global_step % 1000 == 0:
                    ckp_path = os.path.join(params.log_dir, 'model_gs_{}'.format(str(global_step // 1000).zfill(3) + "k"))
                    logger.info('Saving model checkpoint to {}'.format(ckp_path))
                    sv.saver.save(sess, ckp_path)           

            if global_step > params.num_steps:
                break

    logger.info('Completed {} steps!'.format(global_step))
