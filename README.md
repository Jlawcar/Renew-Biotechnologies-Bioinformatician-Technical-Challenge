# Dorado Crossover Pipeline

Aligns a BAM file to an expected reference and one or more crossover references in parallel, then reports what percentage of reads mapped to each.

---

## Requirements

- Nextflow
- Dorado
- Samtools
- Python
---

## Project Structure

```
my-pipeline/
├── main.nf
└── bin/
    └── crossover_percent.py
```

---

## Usage

```bash
nextflow run main.nf \
    --bam       reads.bam \
    --expected  expected_ref.fa \
    --crossover "ref1.fa,ref2.fa,ref3.fa" \
    --outdir    results
```

### Parameters

| Parameter | Required | Description |
|---|---|---|
| `--bam` | Yes | Input BAM file |
| `--expected` | Yes | The expected/primary reference FASTA |
| `--crossover` | Yes | Comma-separated list of crossover reference FASTAs (no spaces) |
| `--outdir` | No | Output directory (default: `results`) |

---

## Output Structure

```
results/
├── expected/
│   └── expected_ref/
│       ├── expected_ref.sorted.bam
│       ├── expected_ref.sorted.bam.bai
│       └── expected_ref.stats.txt
├── crossover/
│   ├── ref1/
│   │   ├── ref1.sorted.bam
│   │   ├── ref1.sorted.bam.bai
│   │   └── ref1.stats.txt
│   ├── ref2/
│   └── ref3/
└── crossover_report/
    ├── crossover_report.tsv    ← per-reference read counts and percentages
    └── crossover_report.log    ← human-readable summary
