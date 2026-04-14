"""Compile inference.proto to Python gRPC stubs."""

import os
import subprocess
import sys


def build():
    proto_dir = "proto"
    proto_file = os.path.join(proto_dir, "inference.proto")

    subprocess.check_call([
        sys.executable, "-m", "grpc_tools.protoc",
        f"-I{proto_dir}",
        f"--python_out={proto_dir}",
        f"--grpc_python_out={proto_dir}",
        proto_file,
    ])

    # Fix relative import in generated gRPC stub so it works as a package
    grpc_stub = os.path.join(proto_dir, "inference_pb2_grpc.py")
    with open(grpc_stub, "r") as f:
        content = f.read()
    content = content.replace(
        "import inference_pb2 as inference__pb2",
        "from . import inference_pb2 as inference__pb2",
    )
    with open(grpc_stub, "w") as f:
        f.write(content)

    print("Proto stubs generated in proto/")


if __name__ == "__main__":
    build()
