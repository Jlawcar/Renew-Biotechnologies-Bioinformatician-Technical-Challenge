#!/usr/bin/env python3
# bin/crossover_percent.py

import argparse
import re
import sys
from pathlib import Path


def parse_mapped_reads(stats_file: Path) -> int:
    """Extract 'reads mapped' from a samtools stats .txt file."""
    with open(stats_file) as fh:
        for line in fh:
            # SN section lines look like:  SN\treads mapped:\t12345
            if line.startswith("SN") and "reads mapped:" in line:
                parts = line.strip().split("\t")
                return int(parts[2])
    raise ValueError(f"Could not find 'reads mapped' in {stats_file}")


def infer_type(stats_file: Path) -> str:
    name = stats_file.name

    if name.startswith("expected."):
        return "expected"

    if name.startswith("crossover."):
        return "crossover"

    raise ValueError(
        f"Cannot infer type (expected/crossover) from filename: {stats_file}"
    )

def main():
    parser = argparse.ArgumentParser(
        description="Calculate percent of reads mapped to crossover references."
    )
    parser.add_argument(
        "--stats", nargs="+", required=True,
        help="One or more samtools stats .txt files"
    )
    parser.add_argument(
        "--out", required=True,
        help="Output TSV report path"
    )
    parser.add_argument(
        "--log", required=True,
        help="Output summary log path"
    )
    args = parser.parse_args()

    results = []
    total_mapped       = 0
    crossover_mapped   = 0
    expected_mapped    = 0

    for stats_path in args.stats:
        f = Path(stats_path).resolve()
        ref_type    = infer_type(f)
        mapped      = parse_mapped_reads(f)
        sample_name = f.stem.replace(".stats", "")

        results.append({
            "sample":  sample_name,
            "type":    ref_type,
            "mapped":  mapped,
        })

        total_mapped += mapped
        if ref_type == "crossover":
            crossover_mapped += expected_mapped
        else:
            expected_mapped += mapped

    # Recalculate cleanly
    crossover_mapped = sum(r["mapped"] for r in results if r["type"] == "crossover")
    expected_mapped  = sum(r["mapped"] for r in results if r["type"] == "expected")
    total_mapped     = crossover_mapped + expected_mapped

    crossover_pct = (crossover_mapped / total_mapped * 100) if total_mapped > 0 else 0.0
    expected_pct  = (expected_mapped  / total_mapped * 100) if total_mapped > 0 else 0.0

    # Sort: expected first, then crossover alphabetically
    results.sort(key=lambda x: (0 if x["type"] == "expected" else 1, x["sample"]))

    # Write TSV
    with open(args.out, "w") as tsv:
        tsv.write("sample\ttype\treads_mapped\tpct_of_total\n")
        for r in results:
            pct = r["mapped"] / total_mapped * 100 if total_mapped > 0 else 0.0
            tsv.write(f"{r['sample']}\t{r['type']}\t{r['mapped']}\t{pct:.4f}\n")

        # Summary footer
        tsv.write("\n")
        tsv.write(f"TOTAL\t\t{total_mapped}\t100.0000\n")
        tsv.write(f"expected_total\t\t{expected_mapped}\t{expected_pct:.4f}\n")
        tsv.write(f"crossover_total\t\t{crossover_mapped}\t{crossover_pct:.4f}\n")

    # Write log
    with open(args.log, "w") as log:
        log.write("=" * 50 + "\n")
        log.write("  Crossover Index Report\n")
        log.write("=" * 50 + "\n\n")
        log.write(f"  Total reads mapped (all refs) : {total_mapped:>12,}\n")
        log.write(f"  Expected ref reads mapped     : {expected_mapped:>12,}  ({expected_pct:.2f}%)\n")
        log.write(f"  Crossover reads mapped        : {crossover_mapped:>12,}  ({crossover_pct:.2f}%)\n")
        log.write("\n  Per-reference breakdown:\n")
        for r in results:
            pct = r["mapped"] / total_mapped * 100 if total_mapped > 0 else 0.0
            log.write(f"    [{r['type']:>9}]  {r['sample']:<30} {r['mapped']:>10,}  ({pct:.2f}%)\n")
        log.write("\n" + "=" * 50 + "\n")

    print(f"Report written to: {args.out}")
    print(f"Log written to:    {args.log}")


if __name__ == "__main__":
    main()