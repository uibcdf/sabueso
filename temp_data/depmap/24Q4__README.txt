# DepMap Public 24Q4

##############
## Overview ##
##############

This DepMap Release contains new cell models and data from Whole Genome/Exome Sequencing (Copy Number and Mutation), RNA Sequencing (Expression and Fusions), Genome-wide CRISPR knockout screens. Also included are updated metadata and mapping files for information about cell models and data relationships, respectively. Each release may contain improvements to our pipelines that generate this data so you may notice changes from the last release.

###############
## Pipelines ##
###############

### Achilles

This Achilles dataset contains the results of genome-scale CRISPR knockout screens for Achilles (using Avana Cas9 and Humagne-CD Cas12 libraries) and Achilles combined with Sanger's Project SCORE (KY Cas9 library) screens.  

The dataset was processed using the following steps:
- Sum raw readcounts by SequenceID and collapse pDNAs by median (removing sequences with fingerprinting issues, total reads below 500000 or less then 25 mean reads per guide)
- Normalize readcounts such that pDNA sequences have the same mode, and all other sequences have median of nonessentials that matches the median of nonessentials in the corresponding pDNA batch
- Remove intergenic/non-targeting controls, Cas9 guides with multiple alignments to a gene, guides with >5 genomic alignments, and sgRNAs with inconsistent signal (see DropReason of guide maps).
- NA sgRNAs with pDNA counts less than one millionth of the pDNA pool
- Calculate the mean reads per guide for each sequence. Sequences with more then 185 mean reads per guide are considered passing.
- Compute the log2-fold-change (LFC) from pDNA counts for each sequence. Collapse to a gene-level by taking the median of guides.
- Calculate the Null-Normalized Median Difference (NNMD) from the LFC using the following equation: (median(essentials) - medain(nonessentials)) / MAD(nonessentials).  Sequences must be below a threshold of -1.25 to be considered passing.
- Calculate the fraction of reads originating from the other library than what is annotated. The fraction of reads must be below a threshold of 0.1 to be considered passing.
- Calculate residual LFC for each library and replicate by creating a linear model of the replicate's LFC as a function of the mean LFC across replicates. Only genes that show high variance in gene effect across screens and libraries are considered when calculating residual LFC.
- Remove sequences that do not have a Pearson coefficient > .19 with at least one other replicate sequence for the screen using the residual LFC. Remove sequences that have a Pearson coefficient > .8 with any other sequence that is not part of the same screen.
- Calculate the NNMD for each screen after averaging passing sequences. Screen must be below a threshold of -1.25 to be considered passing.
- NA out readcounts for pDNAs which correspond with a SNP in any guide in a vector for a given cell line (to correct ancestry bias), then recompute LFC.
- Compute the naive gene score by collapsing the passing LFC data to a screen x gene matrix.
- Prior to running Chronos, NA apparent outgrowths in readcounts.
- Run Chronos per library-screen type to generate screen-level gene effect scores, apply copy number correction, then scale such that median of common essentials is at -1.0 and median of nonessentials is at 0, and correct for screen quality.  To correct proximity bias, the median gene effect of each chromosome arm is aligned to be the same across all screens. See Venceti et al. 2024 (https://doi.org/10.1186/s13059-024-03336-1) for more details on this correction. This produces the integrated CRISPRGeneEffect matrix using Chronos's innate batch correction. Concatenate gene effects from all libraries into a single ScreenGeneEffect matrix.
- Run Chronos jointly on all libraries-screen types to generate model-level gene effect scores, apply copy correction, scale, and correct screen quality as described above.  To correct proximity bias, the median gene effect of each chromosome arm is aligned to be the same across all screens. See Venceti et al. 2024 (https://doi.org/10.1186/s13059-024-03336-1) for more details on this correction. This produces the integrated CRISPRGeneEffect matrix using Chronos's innate batch correction.
- Using the CRISPRGeneEffect, identify pan-dependent genes as those for whom 90% of cell lines rank the gene above a given dependency cutoff. The cutoff is determined from the central minimum in a histogram of gene ranks in their 90th percentile least dependent line.
- For each Chronos gene effect score from both the ScreenGeneEffect and CRISPRGeneEffect, infer the probability that the score represents a true dependency. This is done using an EM step until convergence independently in each screen/model. The dependent distribution is given by the list of essential genes. The null distribution is determined from unexpressed gene scores in those cell lines that have expression data available, and from the nonessential gene list in the remainder.
The essential  and nonessential controls used throughout the analysis are the Hart reference nonessentials and the intersection of the Hart and Blomen essentials. See Hart et al., Mol. Syst. Biol, 2014 and Blomen et al., Science, 2015. They are provided with this release as AchillesCommonEssentialControls.csv and AchillesNonessentialControls.csv.

### Expression

DepMap expression data is quantified from RNAseq files using the GTEx pipelines. A detailed description of the pipelines and tool versions can be found here: https://github.com/broadinstitute/ccle_processing. These are aligned to hg38.

### Copy number

DepMap WGS/WES relative copy number data is generated by running the GATK copy number pipeline aligned to hg38. Tutorials and descriptions of this method can be found here https://software.broadinstitute.org/gatk/documentation/article?id=11682, https://software.broadinstitute.org/gatk/documentation/article?id=11683.
Absolute copy number data from WGS/WES is generated using PureCN (https://scfbm.biomedcentral.com/articles/10.1186/s13029-016-0060-z).

### Mutations

DepMap mutation calls are generated using Mutect2 and annotated and filtered downstream. Variants are aligned to hg38. Detailed documentation can be found here https://storage.googleapis.com/shared-portal-files/Tools/24Q4_Mutation_Pipeline_Documentation.pdf.

### Fusions

DepMap generates RNAseq based fusion calls using the STAR-Fusion pipeline. A comprehensive overview of how the STAR-Fusion pipeline works can be found here: https://github.com/STAR-Fusion/STAR-Fusion/wiki. We run STAR-Fusion version 1.6.0 using the plug-n-play resources available in the STAR-Fusion docs for gencode v29. We run the fusion calling with default parameters except we add the --no_annotation_filter and --min_FFPM 0 arguments to prevent filtering.

###########
## Files ##
###########

### ScreenSequenceMap.csv

Pipeline: Achilles

**_Pre-Chronos_**

Mapping of SequenceIDs to ScreenID and related info.

**Columns:**

- SequenceID
- ScreenID
- ModelConditionID
- ModelID
- ScreenType: 2DS = 2D standard
- Library
- Days
- pDNABatch
- PassesQC
- ExcludeFromCRISPRCombined

### README.txt

README containing descriptions of each file

### ScreenGeneEffect.csv

Pipeline: Achilles

**_Post-Chronos_**

Gene effect estimates for all screens Chronos processed by library, copy number corrected, scaled, screen quality corrected then concatenated.

**Rows:**

- ScreenID

**Columns:**

- Gene 

### ScreenGeneEffectUncorrected.csv

Pipeline: Achilles

**_Post-Chronos_**

Gene effect estimates for all screens Chronos processed by library, then concatenated. No copy number correction or scaling.

**Rows:**

- ScreenID

**Columns:**

- Gene 

### ScreenNaiveGeneScore.csv

Pipeline: Achilles

**_Post-Chronos_**

LFC collapsed by mean of sequences and median of guides, computed per library-screen type then concatenated.

**Rows:**

- ScreenID

**Columns:**

- Gene 

### ScreenGeneDependency.csv

Pipeline: Achilles

**_Post-Chronos_**

Gene dependency probability estimates for all screens Chronos processed by library-screen type, then concatenated.

**Rows:**

- ScreenID

**Columns:**

- Gene 

### CRISPRScreenMap.csv

Pipeline: Achilles

**_Post-Chronos_**

Map from ModelID to all ScreenIDs combined to make up a given model's data in the CRISPRGeneEffect matrix.

**Columns:**

- ModelID
- ScreenID

### CRISPRGeneEffect.csv

Pipeline: Achilles

**_Post-Chronos_**

Gene effect estimates for all models, integrated using Chronos.  Copy number corrected, scaled, and screen quality corrected.

**Rows:**

- ModelID

**Columns:**

- Gene

### CRISPRGeneEffectUncorrected.csv

Pipeline: Achilles

**_Post-Chronos_**

Gene effect estimates for all models, integrated using Chronos. No copy number correction or scaling.

**Rows:**

- ModelID

**Columns:**

- Gene

### CRISPRInferredLibraryEffect.csv

Pipeline: Achilles

**_Post-Chronos_**

The estimates for the library batch effects identified by Chronos.
 
**Rows:**

- LibraryBatch

**Columns:**

- Gene

### CRISPRInitialOffset.csv

Pipeline: Achilles

**_Post-Chronos_**

Estimated log fold pDNA error for each sgrna in each library, as identified by Chronos.

**Rows:**

- sgRNA

**Columns:**

- pDNABatch 


### CRISPRGeneDependency.csv

Pipeline: Achilles

**_Post-Chronos_**

Gene dependency probability estimates for all models in the integrated gene effect.

**Rows:**

- ModelID

**Columns:**

- Gene 


### CRISPRInferredGuideEfficacy.csv

Pipeline: Achilles

**_Post-Chronos_**

The estimates for the efficacies of all reagents in the different libraries-screen types, computed from the Chronos runs.

**Columns:**

- sgRNA
- Efficacy

### CRISPRInferredModelGrowthRate.csv

Pipeline: Achilles

**_Post-Chronos_**

The estimates for the growth rate of all models in the different libraries-screen types, computed from the Chronos runs.

**Columns:**

- ScreenID
- Achilles-Avana-2D
- Achilles-Humagne-CD-2D
- Achilles-Humagne-CD-3D
- Project-Score-KY


### CRISPRInferredModelEfficacy.csv

Pipeline: Achilles

**_Post-Chronos_**

The estimates for the efficacy of all models in the different libraries-screen types, computed from the Chronos runs.

**Columns:**

- ModelID
- Achilles-Avana-2D
- Achilles-Humagne-CD-2D
- Achilles-Humagne-CD-3D
- Project-Score-KY


### CRISPRInferredSequenceOverdispersion.csv

Pipeline: Achilles

**_Post-Chronos_**

List of genes identified as dependencies across all lines. Each entry is separated by a newline.

### CRISPRInferredCommonEssentials.csv

Pipeline: Achilles

**_Post-Chronos_**

List of genes identified as dependencies across all lines. Each entry is separated by a newline.

### AchillesCommonEssentialControls.csv

Pipeline: Achilles

**_Pre-Chronos_**

List of genes used as positive controls, intersection of Biomen (2014) and Hart (2015) essentials. Each entry is separated by a newline.

The scores of these genes are used as the dependent distribution for inferring dependency probability

### AchillesNonessentialControls.csv

Pipeline: Achilles

**_Pre-Chronos_**

List of genes used as negative controls (Hart (2014) nonessentials). Each entry is separated by a newline.

### AvanaRawReadcounts.csv

Pipeline: Achilles

**_Pre-Chronos_**

Summed guide-level read counts for each sequence screened with the Avana Cas9 library.

**Rows:**

- sgRNA

**Columns:**

- SequenceID 

### HumagneRawReadcounts.csv

Pipeline: Achilles

**_Pre-Chronos_**

Summed guide-level read counts for each sequence screened with the Humagne-CD Cas12 library.

**Rows:**

- sgRNA

**Columns:**

- SequenceID 

### KYRawReadcounts.csv

Pipeline: Achilles

**_Pre-Chronos_**

Summed guide-level read counts for each sequence screened with the Sanger's KY Cas9 library.

**Rows:**

- sgRNA

**Columns:**

- SequenceID 

### AvanaLogfoldChange.csv

Pipeline: Achilles

**_Pre-Chronos_**

Log2-fold-change from pDNA counts for each sequence screened with the Avana Cas9 Library.

**Rows:**

- sgRNA

**Columns:**

- SequenceID 

### HumagneLogfoldChange.csv

Pipeline: Achilles

**_Pre-Chronos_**

Log2-fold-change from pDNA counts for each sequence screened with the Humagne-CD Library.

**Rows:**

- sgRNA

**Columns:**

- SequenceID 

### KYLogfoldChange.csv

Pipeline: Achilles

**_Pre-Chronos_**

Log2-fold-change from pDNA counts for each sequence screened with the Sanger's KY Cas9 Library.

**Rows:**

- sgRNA

**Columns:**

- SequenceID 

### AvanaGuideMap.csv

Pipeline: Achilles

**_Pre-Chronos_**

Mapping of sgRNAs to Genes in the Avana Cas9 library.

**Columns:**

- sgRNA: guide in vector
- GenomeAlignment: alignment to hg38
- Gene: HUGO (entrez)
- nAlignments: total number of alignments for a given sgRNA
- UsedByChronos: boolean indicating if sgRNA was included in Chronos analysis
- DropReason: why a guide was removed prior to Chronos analysis


### HumagneGuideMap.csv

Pipeline: Achilles

**_Pre-Chronos_**

Mapping of sgRNAs to Genes in the Humagne-CD Cas12 library.

**Columns:**

- sgRNA: first guide in vector
- GenomeAlignment: alignment of first guide to hg38
- sgRNA2: second guide in vector
- GenomeAlignment2: alignment of second guide to hg38
- Set: which half of the library the vector is part of (C, D, or Both)
- Gene: HUGO (entrez)
- nAlignments: total number of alignments for a given sgRNA
- UsedByChronos: boolean indicating if sgRNA was included in Chronos analysis
- DropReason: why a guide was removed prior to Chronos analysis


### KYGuideMap.csv

Pipeline: Achilles

**_Pre-Chronos_**

Mapping of sgRNAs to Genes in the Sanger's KY Cas9 library.

**Columns:**

- sgRNA: guide in vector
- GenomeAlignment: alignment to hg38
- Gene: HUGO (entrez)
- nAlignments: total number of alignments for a given sgRNA
- UsedByChronos: boolean indicating if sgRNA was included in Chronos analysis
- DropReason: why a guide was removed prior to Chronos analysis


### AchillesScreenQCReport.csv

Pipeline: Achilles

**_Pre-Chronos_**

Screen-level quality control metrics.

**Columns:**

- ScreenID
- ScreenNNMD: null-normalized median difference (threshold of -1.25)
- ScreenROCAUC: area under the Receiver Operating Characteristic curve 
for essential (positive) vs nonessentials (negative) controls
- ScreenFPR: false positive rate, computed as fraction of nonessentials in
the 15th percentile most depleted genes
- ScreenMeanEssentialDepletion: mean LFC of essentials
- ScreenMeanNonessentialDepletion: mean LFC of nonessentials
- ScreenSTDEssentials: standard deviation of essential gene LFCs
- ScreenSTDNonessentials: standard deviation of nonessential gene LFCs
- PassesQC: boolean indicating if screen passes QC thresholds
- CanInclude: boolean indicating if screen can be included in dataset
- QCStatus: string describing QC status
- HasCopyNumber: boolean indicating if screen has copy number data
- ModelConditionID
- ModelID
- Library
- ScreenType
- CasActivity: percentage of cells remaining GFP negative on days 12-14 of cas9
  activity assay as measured by FACs
- ScreenDoublingTime: hours for cells to double
- nPassingSequences: number of sequences that pass sequence-level QC
- nIncludedSequences: number of sequences that can be included


### AchillesSequenceQCReport.csv

Pipeline: Achilles

**_Pre-Chronos_**

Sequence-level quality control metrics.

**Columns:**

- SequenceID
- SequenceTotalReads: total number of raw readcounts
- SequenceMeanReadsPerGuide: mean reads per guide following normalization (threshold of 185)
- SequenceNNMD: null-normalized median difference (threshold of -1.25)
- PassesQC: boolean indicating if sequence passes QC thresholds
- CanInclude: boolean indicating if sequence can be included in dataset
- QCStatus: string describing QC status
- SequenceMaxCorr: max correlation of residual LFC with other 
sequences from same screen (threshold of 0.19)
- SequenceFracReadsFromOtherLibrarySubset: the fraction of reads originating from a library other than what is annotated (threshold of 0.1)
- UnexpectedHighCorrelation: max correlation of residual LFC with other 
sequences that are not from the same screen (threshold of 0.8)
- UnexpectedHighCorrelationPartners: list of sequences that are highly correlated 
with sequences that are not from the same screen (threshold of 0.8)
- ConfirmedNoSwap: confirms a sample swap did not occur and overrides QC failure due to high correlation with random sequences reported in column “UnexpectedHighCorrelationPartners"
- ScreenID
- ScreenPassesQC: boolean indicating if corresponding screen passes QC thresholds


### AchillesHighVarianceGeneControls.csv

Pipeline: Achilles

**_Pre-Chronos_**

List of genes with variable gene effects across models and libraries. Used for sequence correlation in QC.

### OmicsExpressionGenesExpectedCountProfile.csv

Pipeline: Expression

RNAseq read count data from RSEM (unstranded mode).

**Rows:**

- Profile ID

**Columns:**

- Genes (HGNC symbol and Ensembl ID)

### OmicsExpressionProteinCodingGenesTPMLogp1.csv

Pipeline: Expression

Gene expression TPM values of the protein coding genes for DepMap cell lines.

Values are inferred from RNA-seq data using RSEM (unstranded mode), and are reported after log2 transformation, using a pseudo-count of 1; log2(TPM+1).

Additional RNA-seq-based expression measurements are available for download as part of the full DepMap Data Release.

More information on the DepMap Omics processing pipeline is available at <https://github.com/broadinstitute/depmap_omics>.

### OmicsExpressionProteinCodingGenesTPMLogp1BatchCorrected.csv

Pipeline: Expression

Gene expression TPM values of the protein coding genes for DepMap cell lines.

Values are inferred from RNA-seq data using RSEM (stranded or unstranded mode, depending on each sample's sequencing protocol) and are reported after log2 transformation, using a pseudo-count of 1; log2(TPM+1).

To see if a sample was run using the stranded or unstranded protocol, please refer to OmicsProfiles and OmicsDefaultModelProfiles.

Batch-corrected for strandedness using ComBat <https://academic.oup.com/nargab/article/2/3/lqaa078/5909519>.

Additional RNA-seq-based expression measurements are available for download as part of the full DepMap Data Release.

More information on the DepMap Omics processing pipeline is available at <https://github.com/broadinstitute/depmap_omics>.

### OmicsExpressionProteinCodingGenesTPMLogp1Stranded.csv

Pipeline: Expression

Gene expression TPM values of the protein coding genes for DepMap cell lines sequenced using the stranded protocol.

Values are inferred from RNA-seq data using RSEM (stranded mode) and are reported after log2 transformation, using a pseudo-count of 1; log2(TPM+1).

Additional RNA-seq-based expression measurements are available for download as part of the full DepMap Data Release.

More information on the DepMap Omics processing pipeline is available at <https://github.com/broadinstitute/depmap_omics>.

### OmicsExpressionTranscriptsExpectedCountProfile.csv

Pipeline: Expression

RNAseq read count data from RSEM (unstranded mode).

**Rows:**

- Profile ID

**Columns:**

- Transcripts (HGNC symbol and ensembl transcript ID)

### OmicsExpressionTranscriptsTPMLogp1Profile.csv

Pipeline: Expression

RNAseq transcript tpm data using RSEM (unstranded mode). Log2 transformed, using a pseudo-count of 1.

**Rows:**

- Profile ID

**Columns:**

- Transcripts (HGNC symbol and ensembl transcript ID)

### OmicsExpressionAllGenesTPMLogp1Profile.csv

Pipeline: Expression

Gene expression TPM values of all genes for DepMap cell lines. Values are inferred from RNA-seq data using RSEM (unstranded mode) and are reported after log2 transformation, using a pseudo-count of 1; log2(TPM+1).

Additional RNA-seq-based expression measurements are available for download as part of the full DepMap Data Release.

More information on the DepMap Omics processing pipeline is available at <https://github.com/broadinstitute/depmap_omics>.

**Rows:**

- Profile ID

**Columns:**

- Gene (HGNC symbol and ensembl gene ID)

### OmicsExpressionAllGenesEffectiveLengthProfile.csv

Pipeline: Expression

Gene effective length for all genes output from RSEM (unstranded mode)

**Rows:**

- Profile ID

**Columns:**

- Gene (HGNC symbol and ensembl gene ID)


### OmicsExpressionRNASeQCGeneCountProfile.csv

Pipeline: Expression

Gene count outputs from RNASeQC2 <https://github.com/getzlab/rnaseqc> run in unstranded mode.

Gene mapping based on Gencode v29.

**Rows:**

- Profile ID

**Columns:**

- Gene (HGNC symbol and ensembl gene ID)

### OmicsExpressionRNASeQCGeneCountStrandedProfile.csv

Pipeline: Expression

Gene count outputs from RNASeQC2 <https://github.com/getzlab/rnaseqc> with stranded samples only, run in stranded mode.

Gene mapping based on Gencode v29.

**Rows:**

- Profile ID

**Columns:**

- Gene (HGNC symbol and ensembl gene ID)

### OmicsCNSegmentsProfile.csv

Pipeline: Copy number

Segment level copy number data.

**Columns:**

- Profile ID
- Chromosome
- Start (bp start of the segment)
- End (bp end of the segment)
- Num_Probes (the number of targeting probes that make up this segment)
- Segment_Mean (relative copy ratio for that segment)
- Amplification status (+,-,0)

### OmicsCNGene.csv

Pipeline: Copy number

Gene-level copy number data. Inferred from WGS or WES depending on the availability of the data type. Values are calculated by mapping genes onto the segment level calls and computing a weighted average along the genomic coordinate. Genomic coordinates are first mapped to ENSG IDs using biomart (nov2020) and to Hugo symbols and Entrez IDs using Gene.csv.

Genes that overlap with segmental duplication regions and/or flagged by repeatMasker are masked in this matrix. For details see https://github.com/broadinstitute/depmap_omics/blob/master/docs/source/dna.md#masking.

Additional copy number datasets are available for download as part of the full DepMap Data Release.

More information on the DepMap Omics processing pipeline is available at <https://github.com/broadinstitute/depmap_omics>.

### PortalOmicsCNGeneLog2.csv

A log2(x+1) transformed version of OmicsCNGene.csv for use in the portal's Data Explorer and custom analysis tools.

### OmicsFusionFiltered.csv

Pipeline: Fusions

Gene fusion data derived from RNAseq data. Data is filtered using by performing the following:

- Removing fusion involving HLA genes or those whose both breakends are on the mitochondrial chromosome
- Removed common false positive fusions (red herring annotations as described in the STAR-Fusion docs)
- Recurrent fusions observed in CCLE across cell lines (in 10% or more of the samples)
- Removed fusions where SpliceType='INCL_NON_REF_SPLICE' and LargeAnchorSupport='NO_LDAS' and FFPM < 0.1
- FFPM < 0.05

Column descriptions can be found in the STAR-Fusion wiki, except for CCLE_count, which indicates the number of CCLE samples that have this fusion.

### OmicsFusionUnfilteredProfile.csv

Pipeline: Fusions

Gene fusion data derived from RNAseq data. Data is unfiltered. Column descriptions can be found in the STAR-Fusion wiki.

Samples are identified by Profile IDs.

### OmicsSomaticMutations.csv

Pipeline: Mutations

MAF-like file containing information on all the somatic point mutations and indels called in the DepMap cell lines. 
The calls are generated from Mutect2. 

Additional processed mutation matrices containing genotyped mutation calls are available for download as part of the full DepMap Data Release.

**Columns:**

- Chrom
- Pos
- Ref
- Alt
- AF
- DP
- RefCount
- AltCount
- GT
- PS
- VariantType
- VariantInfo
- DNAChange
- ProteinChange
- HugoSymbol
- EnsemblGeneID
- EnsemblFeatureID
- HgncName
- HgncFamily
- UniprotID
- DbsnpRsID
- GcContent
- LofGeneName
- LofGeneId
- LofNumberOfTranscriptsInGene
- LofPercentOfTranscriptsAffected
- NMD
- MolecularConsequence
- VepImpact
- VepBiotype
- VepHgncID
- VepExistingVariation
- VepManeSelect
- VepENSP
- VepSwissprot
- Sift
- Polyphen
- GnomadeAF
- GnomadgAF
- VepClinSig
- VepSomatic
- VepPliGeneValue
- VepLofTool
- OncogeneHighImpact
- TumorSuppressorHighImpact
- TranscriptLikelyLof
- Brca1FuncScore
- CivicID
- CivicDescription
- CivicScore
- LikelyLoF
- HessDriver
- HessSignature
- RevelScore
- PharmgkbId
- DidaID
- DidaName
- GwasDisease
- GwasPmID
- GtexGene
- ProveanPrediction
- AMClass
- AMPathogenicity
- Hotspot
- Rescue
- EntrezGeneID
- ModelID

For details, see https://storage.googleapis.com/shared-portal-files/Tools/24Q4_Mutation_Pipeline_Documentation.pdf


### OmicsSomaticMutationsProfile.csv

Pipeline: Mutations

MAF-like formatted file containing information on all the somatic point mutations and indels called in the DepMap cell lines. 

Calls are generated from Mutect2.

Additional processed mutation matrices containing genotyped mutation calls are available for download as part of the full DepMap Data Release.

Samples are identified by Profile IDs.

**Columns:**

- Chrom
- Pos
- Ref
- Alt
- AF
- DP
- RefCount
- AltCount
- GT
- PS
- VariantType
- VariantInfo
- DNAChange
- ProteinChange
- HugoSymbol
- EnsemblGeneID
- EnsemblFeatureID
- HgncName
- HgncFamily
- UniprotID
- DbsnpRsID
- GcContent
- LofGeneName
- LofGeneId
- LofNumberOfTranscriptsInGene
- LofPercentOfTranscriptsAffected
- NMD
- MolecularConsequence
- VepImpact
- VepBiotype
- VepHgncID
- VepExistingVariation
- VepManeSelect
- VepENSP
- VepSwissprot
- Sift
- Polyphen
- GnomadeAF
- GnomadgAF
- VepClinSig
- VepSomatic
- VepPliGeneValue
- VepLofTool
- OncogeneHighImpact
- TumorSuppressorHighImpact
- TranscriptLikelyLof
- Brca1FuncScore
- CivicID
- CivicDescription
- CivicScore
- LikelyLoF
- HessDriver
- HessSignature
- RevelScore
- PharmgkbId
- DidaID
- DidaName
- GwasDisease
- GwasPmID
- GtexGene
- ProveanPrediction
- AMClass
- AMPathogenicity
- Hotspot
- Rescue
- EntrezGeneID
- ProfileID

For details, see https://storage.googleapis.com/shared-portal-files/Tools/24Q4_Mutation_Pipeline_Documentation.pdf


### OmicsSomaticMutationsMAFProfile.maf

Pipeline: Mutations

MAF file containing information on all the somatic point mutations and indels called in the DepMap cell lines. 

Calls are generated from Mutect2. 

Additional processed mutation matrices containing genotyped mutation calls are available for download as part of the full DepMap Data Release.

This file contains the same variants as OmicsSomaticMutationsProfile.csv, but follows the standard MAF format suitable for downstream analysis tools such as maftools.

Samples are identified by Profile IDs.

### OmicsSomaticMutationsMatrixHotspot.csv

Pipeline: Mutations

Genotyped matrix determining for each cell line whether each gene has at least one hot spot mutation.

A variant is considered a hot spot if it's present in one of the following: Hess et al. 2019 paper, OncoKB hotspot, COSMIC mutation significance tier 1.
(0 == no mutation; If there is one or more hot spot mutations in the same gene for the same cell line, the allele frequencies are summed, and if the sum is greater than 0.95, a value of 2 is assigned and if not, a value of 1 is assigned.)

### OmicsSomaticMutationsMatrixDamaging.csv

Pipeline: Mutations

Genotyped matrix determining for each cell line whether each gene has at least one damaging mutation.

A variant is considered a damaging mutation if LikelyLoF == True.
(0 == no mutation; If there is one or more damaging mutations in the same gene for the same cell line, the allele frequencies are summed, and if the sum is greater than 0.95, a value of 2 is assigned and if not, a value of 1 is assigned.)

### OmicsExpressionGeneSetEnrichment.csv

Pipeline: Expression

Single Sample Gene Set Enrichment Analysis. 

Scores were calculated using Single Sample Gene Set Enrichment Analysis based on the z-scores of the log2(tpm + 1) of gene-level expression data.
Details about the R script used to run the analysis can be found here: https://github.com/broadinstitute/ssGSEA2.0

**Rows:**

- Model ID

**Columns:**

- Gene set enrichment pathways

### OmicsExpressionGeneSetEnrichmentProfile.csv

Pipeline: Expression

Single Sample Gene Set Enrichment Analysis.

Scores were calculated using Single Sample Gene Set Enrichment Analysis based on the z-scores of the log2(tpm + 1) of gene-level expression data.
Details about the R script used to run the analysis can be found here: https://github.com/broadinstitute/ssGSEA2.0

**Rows:**

- Profile ID

**Columns:**

- Gene set enrichment pathways

### OmicsProfiles.csv

Profile metadata and ID mapping information for files indexed by Profile ID.

**Rows:**

- ProfileID

**Columns:**

- ProfileID
- ModelID 
- ModelConditionID
- Datatype
- Source
- Product
- Stranded
- WESKit
- SharedToDbgap


### OmicsDefaultModelProfiles.csv

Indicates which profiles are selected in the model-level datasets

**Columns:**

- ModelID 
- ProfileID
- ProfileType (DNA/RNA)

### OmicsDefaultModelConditionProfiles.csv

Indicates which profiles are selected for each model condition in Achilles postprocessing.

**Columns:**

- ModelConditionID 
- ProfileID
- ProfileType (DNA/RNA)

### OmicsGuideMutationsBinaryKY.csv

Binary matrix indicating whether there are mutations in guide locations from the KY library.

KY guide library (same as the one used in project Score) can be accessed from https://score.depmap.sanger.ac.uk/downloads.

**Columns:**

- Chrom 
- Start
- End
- sgRNA 
- ModelID

### OmicsGuideMutationsBinaryHumagne.csv

Binary matrix indicating whether there are mutations in guide locations from the Humangne library.

Humagne guide library can be accessed from Addgene (https://www.addgene.org/pooled-library/broadgpp-human-knockout-humagne/).

**Columns:**

- Chrom
- Start
- End
- sgRNA
- ModelID

### OmicsGuideMutationsBinaryAvana.csv

Binary matrix indicating whether there are mutations in guide locations from the Avana library.

Avana guide library can be accessed from AvanaGuideMap.csv.

**Columns:**

- Chrom
- Start
- End
- sgRNA
- ModelID

### OmicsAbsoluteCNGene.csv

Gene-level absolute copy number data generated from PureCN (https://github.com/lima1/PureCN). Genomic coordinates from the segment level are first mapped to ENSG IDs using biomart (nov2020) and to Hugo symbols and Entrez IDs using Gene.csv.

Details on specific parameters we use to run PureCN can be found in our git repository: https://github.com/broadinstitute/depmap_omics/blob/dev/WGS_pipeline/PureCN_pipeline/README.md.

Genes that overlap with segmental duplication regions and/or flagged by repeatMasker are masked in this matrix. For details see https://github.com/broadinstitute/depmap_omics/blob/master/docs/source/dna.md#masking .

Inferred from WGS or WES depending on the availability of the data type. For certain likely high-ploidy samples, PureCN does not produce predictions without manual curation, so these samples are omitted in this dataset even though we have WGS/WES data for them. Values are calculated by mapping genes onto the segment level calls and selecting the copy number from the segment that has the greatest overlap with each gene.

**Rows:**

- ModelID

**Columns:**

- Genes (HGNC symbol and Entrez ID)

### OmicsAbsoluteCNSegmentsProfile.csv

Segment level absolute copy number data generated using PureCN (https://github.com/lima1/PureCN). For certain likely high-ploidy samples, PureCN does not produce predictions without manual curation, so these samples are omitted in this dataset even though we have WGS/WES data for them. 

Details on specific parameters we use to run PureCN can be found in our 
git repository: https://github.com/broadinstitute/depmap_omics/blob/dev/WGS_pipeline/PureCN_pipeline/README.md. 

**Columns:**

  - ProfileID
  - Chromosome
  - Start (bp start of the segment)
  - End (bp end of the segment)
  - LOH_status (loss of heterozygosity status: LOH, COPY-NEUTRAL LOH, WHOLE ARM COPY-NEUTRAL LOH, or NA)
  - SegmentAbsoluteCN (total absolute copy number for that segment)
  - MinorAlleleAbsoluteCN (minor allele absolute copy number for that segment)


### OmicsLoH.csv

Binary matrix of Loss of Heterozygosity (LoH) status generated from PureCN (https://github.com/lima1/PureCN).

Details on specific parameters we use to run PureCN can be found in our git repository: https://github.com/broadinstitute/depmap_omics/blob/dev/WGS_pipeline/PureCN_pipeline/README.md.

Inferred from WGS or WES depending on the availability of the data type. 1 indicates LOH and 0 indicates no LOH. 

**Rows:**

- ModelID 

**Columns:**

- Genes (HGNC symbol and Entrez ID)

### OmicsSignatures.csv

Model-level genomic signatures extracted from WES and WGS data.

Signatures include Ploidy, Chromosomal Instability (CIN), Whole Genome Doubling (WGD), Loss of Heterozygosity Fraction (LoH Fraction), and Microsatellite Instability (MSI Score).

Ploidy, CIN, WGD, and LoH Fraction are generated using PureCN ( https://github.com/lima1/PureCN ). 

MSI Score is generated by MSIsensor2 ( https://github.com/niu-lab/msisensor2 ).

Aneuploidy score is implemented based on Ben-David 2021 paper ( https://www.nature.com/articles/s41586-020-03114-6 )

**Rows:**

- ModelID

**Columns:**

- MSIScore (float)
- Ploidy (float)
- CIN (float)
- WGD (binary, 1 indicates presence of WGD, 0 otherwise)
- LoHFraction (float)
- Aneuploidy (int)

### OmicsSignaturesProfile.csv

Profile-level genomic signatures extracted from WES and WGS data.

Signatures include Ploidy, Chromosomal Instability (CIN), Whole Genome Doubling (WGD), Loss of Heterozygosity Fraction (LoH Fraction), and Microsatellite Instability (MSI Score).

Ploidy, CIN, WGD, and LoH Fraction are generated using PureCN (https://github.com/lima1/PureCN).

MSI Score is generated by MSIsensor2 (https://github.com/niu-lab/msisensor2).

Aneuploidy score is implemented based on Ben-David 2021 paper (https://www.nature.com/articles/s41586-020-03114-6)

**Rows:**

- ProfileID

**Columns:**

- MSIScore (float)
- Ploidy (float)
- CIN (float)
- WGD (binary, 1 indicates presence of WGS, 0 otherwise)
- LoHFraction (float)
- Aneuploidy (int)

### Model.csv

Metadata describing all cancer models/cell lines which are referenced by a dataset contained within the DepMap portal.

- ModelID: Unique identifier for the model

- PatientID: Unique identifier for models derived from the same tissue sample

- CellLineName: Commonly used cell line name

- StrippedCellLineName: Commonly used cell line name without characters or spaces

- DepmapModelType: Abbreviated ID for model type. For cancer models, this field is from Oncotree, information for other disease types are generated by DepMap

- OncotreeLineage: Lineage of model. For cancer models, this field is from Oncotree, information for other disease types are generated by DepMap

- OncotreePrimaryDisease: Primary disease of model. For cancer models, this field is from Oncotree, information for other disease types are generated by DepMap

- OncotreeSubtype: Subtype of model. For cancer models, this field is from Oncotree, information for other disease types are generated by DepMap

- OncotreeCode: For cancer models, this field is based on Oncotree. For some models for which no corresponding code exists, this field is left blank

- PatientSubtypeFeatures: Aggregated features known for the patient tumor

- RRID: Cellosaurus ID

- Age: Age at time of sampling

- AgeCategory: Age category at time of sampling (Adult, Pediatric, Fetus, Unknown)

- Sex: Sex at time of sampling (Female, Male, Unknown)

- PatientRace: Patient/clinical indicated race (not derived)

- PrimaryOrMetastasis: Site of the primary tumor where cancer originated from (Primary, Metastatic, Recurrance, Other, Unknown)

- SampleCollectionSite: Site of tissue sample collection

- SourceType: Indicates where model was onboarded from (Commerical, Academic lab, Other)

- SourceDetail: Details on where model was onboarded from

- CatalogNumber: Catalog number of cell model, if commercial

- ModelType: Type of model at onboarding (e.g. Organoid, Cell Line)

- TissueOrigin: Indicates tissue model was derived from (Human, Mouse, Other)

- ModelDerivationMaterial: Indicates what material a model was derived from (Fresh tissue, PDX, Other)

- ModelTreatment: Indicates which virus was used to transform a cell line

- PatientTreatmentStatus: Indicates if sample was collected before, during, or after the patient's cancer treatment (Pre-treatment, Active treatment, Post-treatment, Unknown)

- PatientTreatmentType: Type of treatment patient received prior to, or at the time of, sampling (e.g. chemotherapy, immunotherapy, etc.), if known

- PatientTreatmentDetails: Details about patient treatment

- Stage: Stage of patient tumor

- StagingSystem: Classification system used to categorize disease stage (e.g. AJCC Pathologic Stage), if known

- PatientTumorGrade: Grade (or other marker of proliferation) of the patient tumor, if known

- PatientTreatmentResponse: Any response to treatment, if known

- GrowthPattern: Format model onboarded in (Adherent, Suspension, Organoid, Neurosphere, Neurosphere 2D, Unknown)

- OnboardedMedia: Description of onboarding media

- FormulationID: The unique identifier of the onboarding media 

- SerumFreeMedia: Indicates a non-serum based media (<1% serum)

- PlateCoating: Coating on plate model onboarded in (Laminin, Matrigel, Collagen, None)

- EngineeredModel: Indicates if model was engineered (genetic knockout, genetic knock down, cultured to resistance, other)

- EngineeredModelDetails: Detailed information for genetic knockdown/out models

- CulturedResistanceDrug: Drug of resistance used for cultured to resistance models

- PublicComments: Comments released to portals

- CCLEName: CCLE name for the cell line

- HCMIID: Identifier models available through the Human Cancer Models Initiative (HCMI)

- ModelAvailableInDbgap: Indicates the availability of data for a Model on DbGaP. Refer to the “SharedToDbgap” column on OmicsProfile.csv for specific Omics Profile data available

- ModelSubtypeFeatures: Curated list of confirmed molecular features seen in the model

- WTSIMasterCellID: WTSI ID

- SangerModelID: Sanger ID

- COSMICID: Cosmic ID



### ModelCondition.csv

The condition(s) under which the model was assayed.

- ModelConditionID: Unique identifier for each model condition. 

- ModelID: Unique identifier for each model (same ID as in model table)

- ParentModelConditionID: ID of parental model condition for new model conditions derived from other model conditions

- DataSource: Site where source data was generated (e.g. Broad, etc.)

- CellFormat: Format the cell line is being grown in (Adherent, Suspension, Mixed, Organoid, Neurosphere, Unknown). This can be different from Growth Pattern.

- Morphology: Description of morphological features of the model in a particular growth condition

- PassageNumber: Number of cell line passages (<5, 6-10, 10+)

- GrowthMedia: Media condition was grown in at the model condition level

- FormulationID: Media formulation

- PlateCoating: Substrate used to coat plates (Laminin, Matrigel, None, Unknown)

- SerumFreeMedia: Indicates a non-serum based media (<1% serum)

- PrescreenTreatmentDrug: Drug used in pretreatment prior to screening

- PrescreenTreatmentDrugDays: Duration of drug treatment prior to screening 

- AnchorDrug: Name of drug treatment used in anchor screen

- AnchorDrugConcentration: Concentration of drug treatment used in anchor screen (with units)

- AnchorDaysWithDrug: Range of days the model was treated with drug in anchor screens



### OmicsMicrosatelliteRepeatsProfile.csv

Weighted mean of the number of motif repeats predicted by [MSIsensor2](https://github.com/niu-lab/msisensor2) at each microsatellite site. This data is upstream of MSIscore in OmicsSignatures.

Indexed by ProfileID

### OmicsExpressionAllGenesTPMLogp1StrandedProfile.csv

Gene expression TPM values of all genes for stranded DepMap cell lines. Values are inferred from RNA-seq data using RSEM (stranded mode) and are reported after log2 transformation, using a pseudo-count of 1; log2(TPM+1).

Additional RNA-seq-based expression measurements are available for download as part of the full DepMap Data Release.

More information on the DepMap Omics processing pipeline is available at <https://github.com/broadinstitute/depmap_omics>.

**Rows:**

- Profile ID

**Columns:**

- Gene (HGNC symbol and ensembl gene ID)

### OmicsExpressionTranscriptsTPMLogp1StrandedProfile.csv

RNAseq transcript tpm data for stranded samples using RSEM (stranded mode). Log2 transformed, using a pseudo-count of 1.

**Rows:**

- Profile ID

**Columns:**

- Transcripts (HGNC symbol and ensembl transcript ID)

### OmicsExpressionGenesExpectedCountStrandedProfile.csv

RNAseq read count data for stranded samples from RSEM (stranded mode).

**Rows:**

- Profile ID

**Columns:**

- Genes (HGNC symbol and Ensembl ID)

### OmicsExpressionTranscriptsExpectedCountStrandedProfile.csv

RNAseq read count data for stranded samples from RSEM (stranded mode).

**Rows:**

- Profile ID

**Columns:**

- Transcripts (HGNC symbol and ensembl transcript ID)

### Gene.csv

This file contains the metadata about all genes which are loaded into the DepMap portal's database. Most pipelines will now use this table for mapping between various gene and protein identifiers as we work to get them all switched over. This file will be used to ensure all files have consistent gene symbols and other gene identifiers. 

This table was taken from the quarterly export the gene information published by HGNC and downloaded from https://www.genenames.org/download/archive/quarterly/tsv/


### PortalCompounds.csv

This file contains the metadata on all compounds which is loaded into the DepMap portal along with the set of IDs used in the original drug screens data files which transformed and loaded into the portal. Several columns may be blank for compounds used by older drug screens. As new drugs are added we're curating metadata, but still need to backfill these columns for past drug screens.

Columns:
* CompoundID: The internal DepMap portal compound ID
* CompoundName: The canonical name of the compound which will be shown as the default name for the compound
* GeneSymbolOfTargets: A ";" delimited list of gene symbols which are targets of this compound
* TargetOrMechanism: A brief description of the targets and/or mechanism
* Synonyms: A ";" delimited list of alternative names of this compound
* SampleIDs: A ";" delimited list of IDs used to reference this compound in different drug datasets. Each ID is prefixed with an abbreviation representing which data source used the ID
* ChEMBLID: ChEMBLID for this compound taken from PubChem (only populated for those compounds which have PubChemCID populated)
* SMILES: Canonical SMILES string describing molecular structure of the compound taken from PubChem (only populated for those compounds which have PubChemCID populated)
* InChIKey: InChIKey taken from PubChem (only populated for those compounds which have PubChemCID populated)
* DoseUnit: Either "uM" or "mg/mL" 
* PubChemCID: PubChem Compound ID 



