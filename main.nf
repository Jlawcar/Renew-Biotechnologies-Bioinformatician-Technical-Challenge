// main.nf
nextflow.enable.dsl=2

// ---------- parameters ----------
params.bam       = null    // --bam reads.bam
params.expected  = null    // --expected expected.fa
params.crossover = null    // --crossover "ref1.fa,ref2.fa,ref3.fa"
params.outdir    = "results"

// ---------- processes ----------

process DORADO_ALIGN {
    tag "${type}/${ref.simpleName}"
    publishDir (
        path:{"${params.outdir}/${type}/${ref.simpleName}"},
        mode: 'copy'
    )

    input:
    tuple val(type), path(bam), path(ref)

    output:
    tuple val(type), val("${ref.simpleName}"), path("*.sorted.bam")

    script:
    def prefix = ref.simpleName
    """
    ~/dorado-2.0.0-linux-x64/bin/dorado aligner ${ref} ${bam} \
        | samtools sort -o ${prefix}.sorted.bam
    """
}

process INDEX_BAM {
    tag "${type}/${sample}"
    publishDir (
        path:{"${params.outdir}/${type}/${sample}"}, 
        mode: 'copy'
    )

    input:
    tuple val(type), val(sample), path(bam)

    output:
    tuple val(type), val(sample), path(bam), path("*.bai")

    script:
    """
    samtools index ${bam}
    """
}

process SAMTOOLS_STATS {
    tag "${type}/${sample}"
    publishDir (
        path:{"${params.outdir}/${type}/${sample}"}, 
        mode: 'copy'
    )
    input:
    tuple val(type), val(sample), path(bam), path(bai)

    output:
    tuple val(type), val(sample), path("${type}.${sample}.stats.txt")

    script:
    """
    samtools stats ${bam} > ${type}.${sample}.stats.txt
    """
}

process CROSSOVER_REPORT {
    publishDir (
        path:{"${params.outdir}/crossover_report"}, 
        mode: 'copy'
    )

    input:
    path stats_files

    output:
    path "crossover_report.tsv"
    path "crossover_report.log"

    script:
    """
    cp ${projectDir}/bin/crossover_percent.py .
    python3 crossover_percent.py \
        --stats ${stats_files} \
        --out   crossover_report.tsv \
        --log   crossover_report.log
    """
}

// ---------- workflow ----------
workflow {
    bam_ch = Channel.fromPath(params.bam, checkIfExists: true)

    expected_ch = Channel.fromPath(params.expected, checkIfExists: true)
        .map { ref -> tuple('expected', ref) }

    crossover_ch = Channel.fromPath(
                       params.crossover.split(',').toList(),
                       checkIfExists: true
                   )
        .map { ref -> tuple('crossover', ref) }

    stats_ch = bam_ch
        .combine(expected_ch.mix(crossover_ch))
        .map { bam, type, ref -> tuple(type, bam, ref) }
        | DORADO_ALIGN
        | INDEX_BAM
        | SAMTOOLS_STATS

    all_stats = stats_ch
        .map { type, sample, statsfile -> statsfile }
        .collect()

    CROSSOVER_REPORT(all_stats)

    CROSSOVER_REPORT.out[0].view { tsv ->
        "✔  Crossover report: ${tsv}"
    }
}