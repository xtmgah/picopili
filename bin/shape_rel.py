#! /usr/bin/env python

####################################
# shape_rel.py
# written by Raymond Walters, December 2015
"""
Runs SHAPEIT for GWAS data with related individuals
"""
# Overview:
# 1) Parse arguments
#    - check dependencies, print args, etc
# 2) Align to ref
#    - using extracted ricopili scripts
# 3) Shorten fam file IDs
#    - store fid/iid translations while reading to handle parents
# 4) Split plink files by chr
#    - use shortened IDs
# 5) Run SHAPEIT
#    - using UGER to parallelize
#
####################################



####################################
# Setup
# a) load python dependencies
# b) get variables/arguments
####################################

import sys
#############
if not (('-h' in sys.argv) or ('--help' in sys.argv)):
    print '\n...Importing packages...'
#############

### load requirements
import os
import subprocess
import argparse
# from string import ascii_uppercase
# from glob import glob
# from numpy import digitize
# import random
# import warnings
from args_impute import *
from py_helpers import unbuffer_stdout, link, read_conf #, test_exec
# file_len, read_conf, find_from_path, link, gz_confirm
unbuffer_stdout()


#############
if not (('-h' in sys.argv) or ('--help' in sys.argv)):
    print '\n...Parsing arguments...' 
#############

parser = argparse.ArgumentParser(prog='shape_rel.py',
                                 formatter_class=lambda prog:
                                 argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40),
                                 parents=[parserbase, parserphase, parserref, parsercluster])

args, extra_args = parser.parse_known_args()

# other settings
wd = os.getcwd()
pi_dir = str(wd)+'/pi_sub'
rp_bin = os.path.dirname(os.path.realpath(__file__))
impprep_ex = str(rp_bin) + '/imp_prep.pl'


### print settings in use
print 'Basic settings:'
print '--bfile '+str(args.bfile)
print '--out '+str(args.out)
if args.addout is not None:
    print '--addout '+str(args.out)

print '\nReference Alignment:'
print '--popname '+str(args.popname)
print '--sfh '+str(args.sfh)
print '--fth '+str(args.fth)
print '--ref-info '+str(args.ref_info)

print '\nPrephasing:'
print '--window '+str(args.window)
if args.no_duohmm:
    print '--no-duohmm '
print '--shape-seed '+str(args.shape_seed)

print '\nImputation Reference Files:'
print '--ref-maps '+str(args.ref_maps)
print '--ref-haps '+str(args.ref_haps)
print '--ref-legs '+str(args.ref_legs)
print '--ref-samps '+str(args.ref_samps)

print '\nJob Submission:'
print '--sleep '+str(args.sleep)
print '--mem-req '+str(args.mem_req)
print '--threads '+str(args.threads)



if str(args.addout) != '' and args.addout is not None:
    outdot = str(args.out)+'.'+str(args.addout)
else:
    outdot = str(args.out)


#############
print '\n...Reading ricopili config file...'
#############

### read plink, shapeit loc from config
conf_file = os.environ['HOME']+"/ricopili.conf"
configs = read_conf(conf_file)

plinkx = configs['p2loc']+"plink"
shapeit_ex = configs['shloc'] + '/bin/shapeit'



#############
print '\n...Checking dependencies...'
#############



# TODO: here





print '\n'
print '############'
print 'Begin!'
print '############'

######################
print '\n...Aligning data to reference...'
######################

# TODO: consider restructure to avoid --serial here
prep_log = open(str(outdot) + '.prep.log', 'w')
prep_call = [str(impprep_ex),
             '--serial',
             '--sleep',str(args.sleep),
             '--bim',str(args.bfile)+'.bim',
             '--reffiles',str(args.ref_info),
             '--popname',str(args.popname),
             '--sfh',str(args.sfh),
             '--fth',str(args.fth),
             '--outname',str(outdot)]

print ' '.join(prep_call) + '\n'
subprocess.check_call(prep_call, 
                      stderr=subprocess.STDOUT,
                      stdout=prep_log)
prep_log.close()


######################
print '\n...Shortening .fam ID lengths...'
# - create running dict with translation
# - read each indiv from fam file
# -- if new assign new number, write translation
# -- if old, retrieve translation
# -- write number to new fam file
######################

# read fam file
# load dict with fid, iid, num, indexed by joint id
os.chdir(pi_dir)
infam_file = str(args.bfile) +'.hg19.ch.fl.fam'
outfam_file = str(args.bfile) +'.hg19.ch.fl.fam.idnum'
famtrans_file = str(args.bfile) +'.hg19.ch.fl.fam.transl'

fams = {} # index by fid, value is number
iids = {} # index by fid:iid, value is [fam_number, ind_number]
next_fam = 1
next_iid = 1

fam = open(infam_file, 'r')
outfam = open(outfam_file, 'w')
famtrans = open(famtrans_file, 'w')
for line in fam:
    (fid, iid, pat, mat, sex, phen) = line.split()
    
    # set inidividual key
    joint_id = str(fid)  + ':' + str(iid)
    
    # get fid translation
    if str(fid) not in fams:
        fid_num = next_fam
        fams[str(fid)] = fid_num
        next_fam += 1
    else:
        fid_num = fams[str(fid)]

    # get iid translation
    # need check existence in case is parent of previous
    if str(joint_id) in iids:
        id_num = iids[str(joint_id)][1]
    else:
        id_num = next_iid
        next_iid += 1
        # record translation
        iids[str(joint_id)] = [fid_num, id_num]
        famtrans.write("%d %d %s %s\n" % (fid_num, id_num, str(fid), str(iid)))
    
    # also translate pat/mat ids, if present
    if str(pat) != '0':
        joint_pat = str(fid)  + ':' + str(pat)
        if str(joint_pat) in iids:
            pat_num = iids[str(joint_pat)][1]
        else:
            pat_num = next_iid
            next_iid += 1
            iids[str(joint_pat)] = [fid_num, pat_num] 
            famtrans.write("%d %d %s %s\n" % (fid_num, pat_num, str(fid), str(pat)))
    else:
        pat_num = 0

    if str(mat) != '0':
        joint_mat = str(fid)  + ':' + str(mat)
        if str(joint_mat) in iids:
            mat_num = iids[str(joint_mat)][1]
        else:
            mat_num = next_iid
            next_iid += 1
            iids[str(joint_mat)] = [fid_num, mat_num]
            famtrans.write("%d %d %s %s\n" % (fid_num, mat_num, str(fid), str(mat)))
    else:
        mat_num = 0

    # write translated fam entry
    outfam.write("%d %d %d %d %s %s\n" % (fid_num, id_num, pat_num, mat_num, str(sex), str(phen)))    
    
fam.close()
outfam.close()
famtrans.close()
print 'New fam file written to: %s\n' % (str(pi_dir)+'/'+str(outfam_file))
print 'Fam file translation written to: %s\n' % (str(pi_dir)+'/'+str(famtrans_file))  


######################
print '\n...Splitting by chromosome...'
######################

os.chdir(wd)
os.mkdir('phase_chr')
os.chdir(wd+'/phase_chr')

link(pi_dir + '/' +str(args.bfile) +'.hg19.ch.fl.bed', str(args.bfile) +'.hg19.ch.fl.bed', 'aligned .bed file')
link(pi_dir + '/' +str(args.bfile) +'.hg19.ch.fl.bim', str(args.bfile) +'.hg19.ch.fl.bim', 'aligned .bim file')
link(pi_dir + '/' +str(args.bfile) +'.hg19.ch.fl.fam.idnum', str(args.bfile) +'.hg19.ch.fl.fam', 'aligned .fam file')
link(pi_dir + '/' +str(args.bfile) +'.hg19.ch.fl.fam.transl', str(args.bfile) +'.hg19.ch.fl.fam.transl', 'fam number translation file')

# TODO: handle empty chromosomes
for i in xrange(1,23):
    chr_log = open(str(outdot) + '.chr' + str(i) + '.log', 'w')
    chr_call = [plinkx,
                '--bfile', str(args.bfile) + '.hg19.ch.fl',
                '--chr', str(i),
                '--make-bed',
                '--silent',
                '--memory', str(2000),
                '--out', str(args.bfile) + '.hg19.ch.fl.chr' + str(i)]
    
    if i == 1:
        print ' '.join(chr_call)
    else:
        print 'Chr '+str(i)+'...'

    subprocess.check_call(chr_call,
                          stderr=subprocess.STDOUT,
                          stdout=chr_log)                          
    chr_log.close()


######################
print '\n...Submitting SHAPEIT jobs...'
######################

if args.no_duohmm:
    duo_txt = ''
else:
    duo_txt = '--duohmm'

# TODO: handle empty chromosomes
chrstem = str(args.bfile)+'.hg19.ch.fl.chr\$tasknum'
outstem = str(outdot)+'.chr\$tasknum'
map_arg = str(args.ref_maps).replace('###','\$tasknum')
hap_arg = str(args.ref_haps).replace('###','\$tasknum')
leg_arg = str(args.ref_legs).replace('###','\$tasknum')
samp_arg = str(args.ref_samps).replace('###','\$tasknum')

shape_call = [shapeit_ex,
              '--input-bed', chrstem+'.bed', chrstem+'.bim', chrstem+'.fam',
              '--input-map', map_arg,
              '--input-ref', hap_arg, leg_arg, samp_arg,
              '--window', str(args.window),
              str(duo_txt),
              '--thread', str(args.threads),
              '--seed', str(args.shape_seed),
              '--output-max', outstem+'.phased.haps', outstem+'.phased.sample',
              '--output-log', outstem+'.shape.log']

print ' '.join(shape_call)+'\n'


uger_call = ' '.join(['qsub',
                      '-q','long',
                      '-N', 'shape.'+str(outdot),
                      '-l', 'm_mem_free='+str(args.mem_req)+'g,h_vmem='+str(args.mem_req)+'g',
                      '-pe','smp',str(args.threads),
                      '-t', '1-22',
                      '-o', '\'shape.'+str(outdot)+'.chr$TASK_ID.qsub.log\'',
                      str(rp_bin)+'/uger_array.sub.sh',
                      str(args.sleep),
                      ' '.join(shape_call)])

print uger_call
subprocess.check_call(uger_call, shell=True)





###
# submit next imputation task
###
if args.full_pipe:
    ######################
    print '\n...Queuing best-guess script...'
    ######################
    
    os.chdir(wd)
    next_call = str(rp_bin) + '/imp2_rel.py '+' '.join(sys.argv[1:])

    # TODO: consider queue/mem for agg
    imp_log = 'imp_chunks.'+str(outdot)+'.qsub.log'
    uger_imp = ' '.join(['qsub',
                            '-hold_jid','shape.'+str(outdot),
                            '-q', 'short',
                            '-l', 'm_mem_free=8g,h_vmem=8g',
                            '-N', 'imp.chunks.'+str(outdot),
                            '-o', imp_log,
                            str(rp_bin)+'/uger.sub.sh',
                            str(args.sleep),
                            next_call])
    
    print uger_imp + '\n'
    subprocess.check_call(uger_imp, shell=True)




# finish
print '\n############'
print '\n'
print 'SUCCESS!\n'
exit(0)

