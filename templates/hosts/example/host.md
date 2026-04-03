# Host: example
- Type: direct
- SSH: my-gpu-server
- Remote dir: ~/my-project
- Tunnel:
- GPU check: nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits
- GPU threshold: 50
- PATH setup: export PATH=$HOME/.local/bin:$HOME/.cargo/bin:$PATH
- Dependencies: uv sync
