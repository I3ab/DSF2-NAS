import models.darts_searchable as S
import torch
import argparse
import time
import models.search.darts.utils as utils
import torch.backends.cudnn as cudnn
import numpy as np

import glob 
import logging
import sys
import os

def parse_args():
    parser = argparse.ArgumentParser(description='BM-NAS Configuration')

    parser.add_argument('--seed', type=int, default=2, help='random seed')
    # experiment directory
    parser.add_argument('--save', type=str, default='EXP', help='where to save the experiment')

    # dataset and data parallel
    parser.add_argument('--datadir', type=str, help='data directory',
                        default='data/mmimdb/split')
    parser.add_argument('--small_dataset', action='store_true', default=False, help='use mini dataset for debugging')
    parser.add_argument('--num_workers', type=int, help='dataloader CPUs', default=32)
    parser.add_argument('--parallel', help='use several GPUs', action='store_true', default=False)

    # basic learning settings
    parser.add_argument('--batchsize', type=int, help='batch size', default=8)
    parser.add_argument('--epochs', type=int, help='training epochs', default=30)
    parser.add_argument("--drpt", action="store", default=0.1, dest="drpt", type=float, help="dropout")

    # number of input features
    parser.add_argument('--num_input_nodes', type=int, help='total number of modality features', default=6)
    parser.add_argument('--num_keep_edges', type=int, help='cells and steps will have 2 input edges', default=2)

    # for cells and steps and inner representation size
    parser.add_argument('--C', type=int, help='channels for conv layer', default=192)
    parser.add_argument('--L', type=int, help='length after conv and pool', default=16)
    parser.add_argument('--multiplier', type=int, help='cell output concat', default=2)
    parser.add_argument('--steps', type=int, help='cell steps', default=2)
    parser.add_argument('--node_steps', type=int, help='inner node steps', default=1)
    parser.add_argument('--node_multiplier', type=int, help='inner node output concat', default=1)
    
    # number of classes
    parser.add_argument('--num_outputs', type=int, help='output dimension', default=23)
    parser.add_argument('--f1_type', type=str, help="use 'weighted' or 'macro' F1 Score", default='weighted')

    # archtecture optimizer
    parser.add_argument('--arch_learning_rate', type=float, default=3e-4, help='learning rate for arch encoding')
    parser.add_argument('--arch_weight_decay', type=float, default=1e-3, help='weight decay for arch encoding')
    
    # network optimizer and scheduler
    parser.add_argument('--weight_decay', type=float, default=1e-4, help='weight decay')
    parser.add_argument('--eta_max', type=float, help='max learning rate', default=0.001)
    parser.add_argument('--eta_min', type=float, help='min laerning rate', default=0.000001)
    parser.add_argument('--Ti', type=int, help='for cosine annealing scheduler, epochs Ti', default=1)
    parser.add_argument('--Tm', type=int, help='for cosine annealing scheduler, epochs multiplier Tm', default=2)

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    np.random.seed(args.seed)
    cudnn.benchmark = True
    torch.manual_seed(args.seed)
    cudnn.enabled=True
    torch.cuda.manual_seed(args.seed)

    args.save = 'search-{}-{}'.format(args.save, time.strftime("%Y%m%d-%H%M%S"))
    args.save = os.path.join('final_exp/mmimdb', args.save)

    utils.create_exp_dir(args.save, scripts_to_save=None)

    log_format = '%(asctime)s %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.INFO,
            format=log_format, datefmt='%m/%d %I:%M:%S %p')
    fh = logging.FileHandler(os.path.join(args.save, 'log.txt'))
    fh.setFormatter(logging.Formatter(log_format))
    logger = logging.getLogger()
    logger.addHandler(fh)

    logging.info("args = %s", args)

    use_gpu = torch.cuda.is_available()
    device = torch.device("cuda:0" if use_gpu else "cpu")

    mmimdb_searcher = S.MMIMDB_Searcher(args, device, logger)

    logger.info("BM-NAS for MM-IMDB Started.")
    start_time = time.time()
    best_acc, best_genotype = mmimdb_searcher.search()
    time_elapsed = time.time() - start_time

    logger.info("*" * 50)
    logger.info('Searching complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))
    logger.info('Now listing best fusion_net genotype:')
    logger.info(best_genotype)
