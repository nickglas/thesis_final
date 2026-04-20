"""CLI entry point to start a chain service segment as a standalone process."""

import argparse
from src.models.resnet_splits import COARSE_SPLIT_POINTS
from src.services.chain_service import serve


def main():
    parser = argparse.ArgumentParser(
        description="Start one segment of a gRPC chain service"
    )
    parser.add_argument(
        "--segment_index", required=True, type=int,
        help="0-based index of this segment in the chain",
    )
    parser.add_argument(
        "--split_points", nargs="*", default=[],
        choices=list(COARSE_SPLIT_POINTS),
        help="Ordered coarse split points defining the chain (empty for monolithic)",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=50051)
    parser.add_argument(
        "--next_address", default=None,
        help="host:port of the next service (omit for last segment)",
    )
    parser.add_argument(
        "--max_message_bytes", type=int, default=16 * 1024 * 1024,
    )
    args = parser.parse_args()
    serve(
        segment_index=args.segment_index,
        split_points=args.split_points,
        host=args.host,
        port=args.port,
        next_address=args.next_address,
        max_message_bytes=args.max_message_bytes,
    )


if __name__ == "__main__":
    main()
