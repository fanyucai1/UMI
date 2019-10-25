import os
import subprocess
import sys
fgbio="/software/fgbio/fgbio-1.0.0.jar"
java="java"
picard="/software/picard/picard.jar"
bwa="/software/bwa/bwa-0.7.17/bwa"
ref="/data/Database/hg19/ucsc.hg19.fasta"
samtools="/software/samtools/samtools-v1.9/bin/samtools"
env="export PATH=/software/vardict/VarDict-1.6.0/bin:$PATH"

def run(pe1,pe2,outdir,prefix,readlength):
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    out=outdir+"/"+prefix
    len=int(readlength)-5

    ##########fastq2bam#####################
    if not os.path.exists("%s.unmapped.bam"%(out)):
        cmd="%s -Xmx50g -jar %s FastqToSam F1=%s F2=%s O=%s.unmapped.bam SM=%s RG=%s LB=%s PL=illumina" %(java,picard,pe1,pe2,out,prefix,prefix,prefix)
        subprocess.check_call(cmd,shell=True)

    ##########ExtractUmisFromBam##############
    if not os.path.exists("%s.umi.unmapped.bam"%(out)):
        cmd="%s -Xmx50g -jar %s ExtractUmisFromBam -i %s.unmapped.bam -o %s.umi.unmapped.bam -r 3M2S%sT 3M2S%sT --molecular-index-tags ZA ZB -s RX"\
            %(java,fgbio,out,out,len,len)
        subprocess.check_call(cmd,shell=True)

    ##########align reads######################
    if not os.path.exists("%s.merge.bam"%(out)):
        cmd="%s -Xmx50g -jar %s SamToFastq I=%s.umi.unmapped.bam INTERLEAVE=true F=%s.fq"%(java,picard,out,out)
        subprocess.check_call(cmd,shell=True)
        cmd="%s mem -p -t 10 %s %s.fq >%s.mapped.bam"%(bwa,ref,out,out)
        subprocess.check_call(cmd,shell=True)
        cmd="%s -Xmx50g -jar %s MergeBamAlignment UNMAPPED=%s.umi.unmapped.bam ALIGNED=%s.mapped.bam O=%s.merge.bam R=%s SO=coordinate MAX_GAPS=-1 ORIENTATIONS=FR VALIDATION_STRINGENCY=SILENT " \
            "ALIGNER_PROPER_PAIR_FLAGS=true CREATE_INDEX=true" %(java,picard,out,out,out,ref)
        subprocess.check_call(cmd,shell=True)

    ########GroupReadsByUmi####################
    if not os.path.exists("%s.umi.stat.umi_counts.txt"%(out)):
        cmd="%s -Xmx50g -jar %s GroupReadsByUmi -i %s.merge.bam  -o %s.group.bam -s Paired -m 20" \
            %(java,fgbio,out,out)
        subprocess.check_call(cmd,shell=True)
        cmd="%s -Xmx50g -jar %s CollectDuplexSeqMetrics -i %s.group.bam -o %s.umi.stat -u true  -a 3 -b 3" \
            %(java,fgbio,out,out)
        subprocess.check_call(cmd,shell=True)

    #######Combine each set of reads to generate consensus reads##########################
    if not os.path.exists("%s.consensus.unmapped.bam"%(out)):
        cmd="%s -Djava.io.tmpdir=/data/tmp -Xmx50g -jar %s CallDuplexConsensusReads -i %s.group.bam -o %s.consensus.unmapped.bam -1 45 -2 30 -m 30 --threads 20 -M 1 0 0" \
            %(java,fgbio,out,out)
        subprocess.check_call(cmd,shell=True)

    ##############Produce variant calls from consensus reads#################################
    if not os.path.exists("%s.consensus.bam"%(out)):
        cmd="%s -Xmx50g -jar %s SamToFastq I=%s.consensus.unmapped.bam F=%s.consensus.fq INTERLEAVE=true"%(java,picard,out,out)
        subprocess.check_call(cmd,shell=True)
        cmd="%s mem -p -t 10 %s %s.consensus.fq >%s.realign.bam"%(bwa,ref,out,out)
        subprocess.check_call(cmd,shell=True)
        cmd="%s -Xmx50g -jar %s MergeBamAlignment UNMAPPED=%s.consensus.unmapped.bam ALIGNED=%s.realign.bam O=%s.consensus.bam R=%s SO=coordinate MAX_GAPS=-1 ORIENTATIONS=FR VALIDATION_STRINGENCY=SILENT " \
            "ALIGNER_PROPER_PAIR_FLAGS=true CREATE_INDEX=true" %(java,picard,out,out,out,ref)
        subprocess.check_call(cmd,shell=True)

    #######Filter consensus reads#############################################################
    if not os.path.exists("%s.consensus.filter.bam"%(out)):
        cmd="%s -Djava.io.tmpdir=/data/tmp -Xmx50g -jar %s FilterConsensusReads -i %s.consensus.bam -o %s.consensus.filter.bam -r %s -M 1 0 0 --reverse-per-base-tags=true " \
            "-N 30 -E 0.05 -e 0.1"%(java,fgbio,out,out,ref)
        subprocess.check_call(cmd,shell=True)

    ########Clip##############################################################################
    if not os.path.exists("%s.consensus.filter.clipped.bam"%(out)):
        cmd="%s -Djava.io.tmpdir=/data/tmp -Xmx50g -jar %s ClipBam -i %s.consensus.filter.bam -o %s.consensus.filter.clipped.bam -r %s --clip-overlapping-reads=true"\
            %(java,fgbio,out,out,ref)
        subprocess.check_call(cmd,shell=True)
if __name__=="__main__":
    if len(sys.argv)!=6:
        print("python3 %s pe1.fq pe2.fq outdir prefix readlength\n"%(sys.argv[0]))
        print("Email:fanyucai1@126.com")
    else:
        pe1=sys.argv[1]
        pe2=sys.argv[2]
        outdir=sys.argv[3]
        prefix = sys.argv[4]
        readlength=sys.argv[5]
        run(pe1,pe2,outdir,prefix,readlength)