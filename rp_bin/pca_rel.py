#! /usr/bin/env python

print '...Importing packages...'
# load requirements
import os
import subprocess
from distutils import spawn
import argparse



# init vars that may be set as functions of others
pcadir = ""

print '...Parsing arguments...' 
# parse arguments
parser = argparse.ArgumentParser(prog='pca_rel.py',
                                 formatter_class=lambda prog:
                                 argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40))
parser.add_argument('--bfile', 
                    type=str,
                    metavar='FILESTEM',
                    help='file stem for input plink bed/bim/fam',
                    required=True)
parser.add_argument('--out',
                    type=str,
                    metavar='OUTNAME',
                    help='base name for output; recommend 4 character stem to match ricopili',
                    required=True)
parser.add_argument('--rel-deg',
                    type=int,
                    metavar='INT',
                    help='relatedness degree threshold for defining \"unrelated\" set',
                    required=False,
                    default=3)
parser.add_argument('--npcs',
                    type=int,
                    metavar='INT',
                    help='number of principal components to compute',
                    required=False,
                    default=10)
parser.add_argument('--pcadir',
                    type=str,
                    metavar='DIRNAME',
                    help='name for PCA output directory, defaults to pca_imus_OUTNAME',
                    required=False)
parser.add_argument('--no_cleanup',
                    action='store_true',
                    help='skip cleanup of interim files')
# parser.add_argument('--plink-ex',
#                    type=str,
#                    metavar='PATH',
#                    help='path to plink executable, read from ~/ricopili.conf if unspecified',
#                    required=False)
parser.add_argument('--rscript-ex',
                    type=str,
                    metavar='PATH',
                    help='path to Rscript executable, tries reading from PATH if unspecified',
                    required=False,
                    default=spawn.find_executable("Rscript"))
parser.add_argument('--primus-ex',
                    type=str,
                    metavar='PATH',
                    help='path to PRIMUS executable',
                    required=False,
                    default=os.environ['HOME']+"/PRIMUS_v1.8.0/bin/run_PRIMUS.pl")
parser.add_argument('--flashpca-ex',
                    type=str,
                    metavar='PATH',
                    help='path to flashpca executable',
                    required=False,
                    default="/humgen/atgu1/fs03/shared_resources/shared_software/bin/flashpca")
parser.add_argument('--smartpca-ex',
                    type=str,
                    metavar='PATH',
                    help='path to smartpca executable',
                    required=False,
                    default="/humgen/atgu1/fs03/shared_resources/shared_software/EIG6.0beta_noreq/bin/smartpca")


args, pass_through_args = parser.parse_known_args()

#set remaining defaults
if args.pcadir == None:
    pcadir = 'pca_imus_' + args.out
else:
    pcadir = args.pcadir
    
wd = os.getcwd()

 

print '...reading ricopili config file...'
### read plink loc from config
# not getting R here since ricopili.conf currently relies on platform info

conf_file = os.environ['HOME']+"/ricopili.conf"

configs = {}
with open(conf_file, 'r') as f:
    for line in f:
        (key, val) = line.split()
        configs[str(key)] = val

plinkx = configs['p2loc']+"plink"



print '...Checking dependencies...'
# R from path
if args.rscript_ex == None:
    raise AssertionError('Unable to find Rscript in search path')
    
# file exists
assert os.path.isfile(args.primus_ex), "PRIMUS not found at %r" % args.primus_ex
assert os.path.isfile(args.flashpca_ex), "FlashPCA not found at %r" % args.flashpca_ex
assert os.path.isfile(args.smartpca_ex), "SmartPCA not found at %r" % args.smartpca_ex
assert os.path.isfile(plinkx), "Plink not found at %r" % plinkx
assert os.path.isfile(args.rscript_ex), "Rscript not found at %r" % args.rscript_ex

# file executable
assert os.access(args.primus_ex, os.X_OK), "FlashPCA not executable (%r)" % args.primus_ex
assert os.access(args.flashpca_ex, os.X_OK), "FlashPCA not executable (%r)" % args.flashpca_ex
assert os.access(args.smartpca_ex, os.X_OK), "FlashPCA not executable (%r)" % args.smartpca_ex
assert os.access(plinkx, os.X_OK), "Plink not executable (%r)" % plinkx
assert os.access(args.rscript_ex, os.X_OK), "Rscript not executable (%r)" % args.rscript_ex



print '############'
print 'Begin!'
print '############\n'

print '...Computing IMUS (unrelated) set...'
primelog = 'primus_' + args.out + '_imus.log'
subprocess.check_call([args.primus_ex,
                       "--file", args.bfile,
                       "--genome",
                       "--degree_rel_cutoff", str(args.rel_deg),
                       "--no_PR",
                       "--plink_ex", plinkx,
                       "--smartpca_ex", args.smartpca_ex,
                       "&>", primelog])

# verify successful output
primedir = os.getcwd() + '/' + args.bfile + '_PRIMUS'
imus_file = args.bfile + '_cleaned.genome_maximum_independent_set'
imus_dirfile = primedir + '/' + imus_file

if not os.path.isdir(primedir):
    raise IOError("Expected PRIMUS output directory %r not found" % primedir)
elif not os.path.isfile(imus_dirfile):
    raise IOError("Failed to create IMUS set (missing %r)" % imus_dirfile)



print '...Setting up PCA directory...'

if not os.path.exists(pcadir):
    os.makedirs(pcadir)

os.chdir(pcadir)

# setup file links
os.symlink(imus_dirfile,imus_file)
os.symlink(wd+'/'+args.bfile+'.bed',args.bfile+'.bed')
os.symlink(wd+'/'+args.bfile+'.bim',args.bfile+'.bim')
os.symlink(wd+'/'+args.bfile+'.fam',args.bfile+'.fam')

# verify links
if not os.path.isfile(imus_file):
    raise IOError("Failed to link IMUS file (%r)" % imus_file)
elif not os.path.isfile(args.bfile+'.bed'):
    raise IOError("Failed to link bed file (%r)" % str(args.bfile+'.bed') )
elif not os.path.isfile(args.bfile+'.bim'):
    raise IOError("Failed to link bim file (%r)" % str(args.bfile+'.bim') )
elif not os.path.isfile(imus_file):
    raise IOError("Failed to link fam file (%r)" % str(args.bfile+'.fam') )



print '...Extracting IMUS set from data...'

bfile_imus = args.bfile + '.imus'
subprocess.check_call([plinkx,
                       "--bfile", args.bfile,
                       "--keep", imus_file,
                       "--freq",
                       "--silent",
                       "--make-bed",
                       "--out", bfile_imus])



print '...Computing PCA with IMUS individuals...'

subprocess.check_call([args.flashpca_ex,
                       "--bfile", bfile_imus,
                       "--ndim", args.npcs,
                       "--outpc",str(args.out+'_imus_pca.pcs.txt'),
                       "--outvec",str(args.out+'_imus_pca.evec.txt'),
                       "--outval",str(args.out+'_imus_pca.eval.txt'),
                       "--outpve",str(args.out+'_imus_pca.pve.txt'),
                       "--outload",str(args.out+'_imus_pca.snpw.txt'),
                       "&>", str('flashpca_'+args.out+'_imus_pca.log')])



print '...Projecting PCs for remaining individuals...'

# label snpweights to setup pca projection
snpw = open(str(args.out+'_imus_pca.snpw.txt'), 'r')
imus_bim = open(str(bfile_imus+'.bim'), 'r')
snpw_out = open(str(args.out+'_imus_pca.snpw.lab.txt'), 'w')

# add bim info to snp weights
for bimline in imus_bim:
    (chrom, snp, cm, bp, a1, a2) = bimline.split()
    snpw_out.write(snp + ' ' + a1 + ' ' + ' '.join(snpw.readline().split()) + '\n')

# note: shell probably faster, but less readable/robust
# cut -f 2,5 file.bim | tr '\t' ' ' | paste -d ' ' - <(cat file_snpw.txt | tr -s ' ' | sed 's/^ //') > file_snpw_labelled.txt

snpw.close()
imus_bim.close()
snpw_out.close()


# project with plink
for pcnum in xrange(1,args.npcs+1):

    pccol = pcnum + 2
    
    subprocess.check_call([plinkx,
                           "--bfile", args.bfile,
                           "--score", str(args.out+'_imus_pca.snpw.lab.txt'), "1", "2", str(pccol), "center",
                           "--read-freq", str(bfile_imus + '.frq'),                           
                           "--silent",
                           "--out", str(args.out + '.projpca.pc' + str(pcnum) )])

# verify all outputs have same length
# wc -l, taken from http://stackoverflow.com/questions/845058
def file_len(fname):
    p = subprocess.Popen(['wc', '-l', fname], stdout=subprocess.PIPE, 
                                              stderr=subprocess.PIPE)
    result, err = p.communicate()
    if p.returncode != 0:
        raise IOError(err)
    return int(result.strip().split()[0])

# list of file names
pc_files_nam = [str(args.out + '.projpca.pc' + str(i) + '.profile') for i in xrange(1,args.npcs+1)]

# nrow for each file
pc_nrows = [file_len(pc_files_nam[i-1]) for i in xrange(1,args.npcs+1)]

# check all equal
if not (pc_nrows.count(pc_nrows[0]) == len(pc_nrows)):
    raise IOError("Projected PCA results files %r not all the same size" % str(args.out + '.projpca.pc[1-' + str(args.npcs) + '].profile'))
    
# combine columns, anchored with fam
bfile_fam = open(str(args.bfile + '.fam'), 'r')
pc_files = [open(pc_files_nam[i], 'r') for i in xrange(0,len(pc_files_nam))]
pc_out_nam = str(args.out + '.projpca.allpcs.txt')
pc_out = open(pc_out_nam, 'w')

# strip headers
dumphead = [pc_files[i].readline() for i in xrange(0,len(pc_files))]

# init output header
pc_out.write('FID IID ' + ' '.join( [str('PC'+str(i)) for i in xrange(1,args.npcs+1)] ) + '\n')

for famline in bfile_fam:
    (fid, iid, mat, pat, sex, phen) = famline.split()
    pc_val = []

    for pcnum in xrange(0,args.npcs):
        (pc_fid, pc_iid, pc_phen, pc_cnt, pc_cnt2, pc_score) = pc_files[pcnum].readline().split()

        if not ( pc_fid == fid and pc_iid == iid):
            raise ValueError("Unexpected FID:IID in %r (%s:%s instead of %s:%s)", pc_files_nam[pcnum], pc_fid, pc_iid, fid, iid )

        else:
            pc_val.append(pc_score)

    pc_out.write(fid + ' ' + iid + ' ' + ' '.join(pc_val) + '\n')

bfile_fam.close()
pc_out.close()
for i in xrange(0,len(pc_files)):
    pc_files[i].close()



print '...Plotting PCs...'

#########
######### add r plotting
#########


if not args.no_cleanup:
    print '...Clean-up interim files...'
    
    subprocess.check_call(["gzip", "-f", pc_out_nam])


print '############'
print '\n'
print 'SUCCESS!\n'
exit(0)
