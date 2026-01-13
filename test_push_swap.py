#!/usr/bin/env python3
import argparse
import random
import subprocess
import sys
from typing import List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run randomized push_swap tests for small input sizes (2-5 numbers)."
    )
    parser.add_argument(
        "--binary",
        default="./push_swap",
        help="Path to the push_swap executable (default: ./push_swap)",
    )
    parser.add_argument(
        "--tests",
        type=int,
        default=200,
        help="Number of random cases to run per size (default: 200)",
    )
    parser.add_argument(
        "--sizes",
        default="2,3,4,5",
        help="Comma-separated list of sizes to test (default: 2,3,4,5)",
    )
    parser.add_argument(
        "--min",
        dest="min_val",
        type=int,
        default=-50,
        help="Minimum integer value for generated inputs (default: -50)",
    )
    parser.add_argument(
        "--max",
        dest="max_val",
        type=int,
        default=50,
        help="Maximum integer value for generated inputs (default: 50)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--show-fail",
        type=int,
        default=5,
        help="How many failing cases to print (default: 5)",
    )
    return parser.parse_args()


def swap(stack: List[int]) -> None:
    if len(stack) >= 2:
        stack[0], stack[1] = stack[1], stack[0]


def push(src: List[int], dst: List[int]) -> None:
    if src:
        dst.insert(0, src.pop(0))


def rotate(stack: List[int]) -> None:
    if len(stack) >= 1:
        stack.append(stack.pop(0))


def reverse_rotate(stack: List[int]) -> None:
    if len(stack) >= 1:
        stack.insert(0, stack.pop())


VALID_OPS = {
    "sa",
    "sb",
    "ss",
    "pa",
    "pb",
    "ra",
    "rb",
    "rr",
    "rra",
    "rrb",
    "rrr",
}


def apply_ops(ops: List[str], start_a: List[int]) -> Tuple[List[int], List[int]]:
    a = start_a.copy()
    b: List[int] = []
    for op in ops:
        if op == "sa":
            swap(a)
        elif op == "sb":
            swap(b)
        elif op == "ss":
            swap(a)
            swap(b)
        elif op == "pa":
            push(b, a)
        elif op == "pb":
            push(a, b)
        elif op == "ra":
            rotate(a)
        elif op == "rb":
            rotate(b)
        elif op == "rr":
            rotate(a)
            rotate(b)
        elif op == "rra":
            reverse_rotate(a)
        elif op == "rrb":
            reverse_rotate(b)
        elif op == "rrr":
            reverse_rotate(a)
            reverse_rotate(b)
        else:
            raise ValueError(f"Unknown operation: {op}")
    return a, b


def is_sorted(stack: List[int]) -> bool:
    return all(stack[i] <= stack[i + 1] for i in range(len(stack) - 1))


def run_case(binary: str, values: List[int]) -> Tuple[bool, str, int]:
    cmd = [binary] + [str(v) for v in values]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, f"non-zero exit ({result.returncode}): {result.stderr.strip()}", 0
    raw_stdout = result.stdout.strip()
    if raw_stdout == "Error":
        return False, "program printed Error", 0

    # Split on any whitespace to tolerate single-line outputs like "sa ra".
    tokens = [tok for tok in raw_stdout.split() if tok]
    unknown = [tok for tok in tokens if tok not in VALID_OPS]
    if unknown:
        snippet = raw_stdout.replace("\n", "\\n")
        return False, f"invalid output token(s): {unknown} (stdout='{snippet}')", len(tokens)

    ops = tokens
    try:
        final_a, final_b = apply_ops(ops, values)
    except Exception as exc:  # pylint: disable=broad-except
        return False, f"operation error: {exc}", len(ops)
    if final_b:
        return False, "stack B not empty after operations", len(ops)
    if not is_sorted(final_a):
        return False, "stack A not sorted after operations", len(ops)
    return True, "", len(ops)


def format_values(values: List[int]) -> str:
    return " ".join(str(v) for v in values)


def main() -> int:
    args = parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    sizes = [int(s) for s in args.sizes.split(",") if s.strip()]
    if any(s < 2 or s > 5 for s in sizes):
        print("Only sizes 2 through 5 are supported", file=sys.stderr)
        return 1
    if args.max_val - args.min_val + 1 < max(sizes):
        print("Range too small for unique numbers of requested size", file=sys.stderr)
        return 1

    total = 0
    failures = []
    for size in sizes:
        for _ in range(args.tests):
            values = random.sample(range(args.min_val, args.max_val + 1), size)
            ok, reason, move_count = run_case(args.binary, values)
            total += 1
            if not ok:
                failures.append(
                    {
                        "size": size,
                        "values": values,
                        "reason": reason,
                        "moves": move_count,
                    }
                )

    print(f"Total tests: {total}")
    print(f"Failures: {len(failures)}")

    if failures:
        print("\nSample failing cases:")
        for fail in failures[: args.show_fail]:
            vals = format_values(fail["values"])
            print(
                f"- size={fail['size']} values=[{vals}] moves={fail['moves']} reason={fail['reason']}"
            )
        print("\nRerun a specific case with:")
        if failures:
            example = failures[0]
            vals = format_values(example["values"])
            print(f"  {args.binary} {vals}")
        return 1

    print("All cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
