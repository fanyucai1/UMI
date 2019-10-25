##  unique molecular identifiers

### UMI分类

UMI 有单端UMI(例如swift)也有双端UMI(例如Illumina TSO500)
UMI 也可以分为固定种类的UMI(例如Illumina TSO500)固定种类是120，双端就是120*120，还有就是随机碱基的UMI，例如swift与IDT（双端随机3碱基长度种类就是64*64）
UMI 添加种类一种是将UMI添加到测序文库的index位置（swift），一种是将UMI添加到测序文库的reads前端（IDT）

### UMI预处理

是指将测序过程中的UMI序列以标签的形式添加到SAM或BAM文件中

实现方法一：

            Illumina下机数据直接从BCL导出到SAM格式，这种情况在实际情况很少遇到不在详细描述
实现方法二：

            以swift试剂提供的单端UMI来讲，由于UMI是位于index的位置而不是在测序读长上，因此在数据拆分时需要将index按照常规fastq的形式输出
            从BCL2fastq数据拆分的时候，需要修改RunInfo.xml和RunParameter.xml这两个文件
            RunInfo.xml：
            <Read Number="2" NumCycles="8" IsIndexedRead="Y" />
            <Read Number="3" NumCycles="8" IsIndexedRead="Y" />
            一般是拆分数据按照单端进行拆分，另一端是将Y修改为N是UMI序列需要输出
            RunParameter.xml:
            <Index2Read>8</Index2Read>
            将Index2去掉改成Read3
            使用fgbio中的AnnotateBamWithUmis
            
            
### fgbio wiki：
https://github.com/fulcrumgenomics/fgbio/wiki

### 单双端UMI

       单端UMI在<------------->CallMolecularConsensusReads

        双端UMI在<------------->CallDuplexConsensusReads

        单端UMI在<------------->GroupReadsByUmi（adjacency）

        双端UMI在<------------->GroupReadsByUmi（paired)

### CallDuplexConsensusReads与FilterConsensusReads

在fgbio中对于ConsensusReads与FilterConsensusReads最小的支持数参数举例--min-reads 10 5 3
In each case if fewer than three values are supplied, the last value is repeated (i.e. 80 40 -> 80 40 40 and 0.1 -> 0.1 0.1 0.1. The first value applies to the final consensus read, the second value to one single-strand consensus, and the last value to the other single-strand consensus. It is required that if values two and three differ, the more stringent value comes earlier.
因此如果你对数据存在链特异性的问题会丢掉很多数据我们目前设置的是--min-reads 1 0 0系统参数是--min-reads 1 1 1


### fastp与UMI
https://github.com/OpenGene/fastp

        fastp --in1 sample.R1.fq --in2 sample.R2.fq -w 10 -U --umi_loc=per_read --umi_len 3 --umi_skip 2 --out1 sample.clean.1.fq --out2 sample.clean.2.fq -l 150 -j out.json -h out.html            
The original read:

        @NS500713:64:HFKJJBGXY:1:11101:1675:1101 1:N:0:TATAGCCT+GACCCCCA
        AAAAAAAAGCTACTTGGAGTACCAATAATAAAGTGAGCCCACCTTCCTGGTACCCAGACATTTCAGGAGGTCGGGAAA
        +
        6AAAAAEEEEE/E/EA/E/AEA6EE//AEE66/AAE//EEE/E//E/AA/EEE/A/AEE/EEA//EEEEEEEE6EEAA
          
After:

        @A00153:435:HNGTVDSXX:1:1101:3712:1000:GCTGTCA_GTCCTCT 1:N:0:GAATTCGT+TTATGAGT

但是如果你使用bcl2fastq,就是分隔符不一样

        @A00153:435:HNGTVDSXX:1:1101:3712:1000:GCTGTCA+GTCCTCT 1:N:0:GAATTCGT+TTATGAGT



