"""CLI entry point to start Service B as a standalone process."""

import argparse
from src.services.service_b import serve


def main():
    parser = argparse.ArgumentParser(description="Start gRPC Service B")
    parser.add_argument("--split_after", required=True,
                        choices=["layer1", "layer2", "layer3", "layer4"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50051)
    parser.add_argument("--max_message_bytes", type=int, default=16 * 1024 * 1024)
    args = parser.parse_args()
    serve(args.split_after, args.host, args.port, args.max_message_bytes)


if __name__ == "__main__":
    main()
