# pingCheck

A Go tool for network pings (ICMP/UDP) with interval and statistics.

## Known Issues

### ICMP Permission Error

When running the tool with ICMP (default mode), you may see an error like:

```
ERROR: listen ip4:icmp : socket: operation not permitted
```

#### Why does this happen?
Sending ICMP packets requires root privileges (or special capabilities) on most Unix-like systems, including Linux and WSL2. Regular users cannot open raw sockets for ICMP.

#### How to fix
- **Run as root:**
  ```bash
  sudo go run main.go -host 10.5.22.1
  ```
- **Use UDP mode (no root required):**
  ```bash
  go run main.go -host 10.5.22.1 -udp
  ```
  (Note: UDP "ping" is not exactly the same as ICMP ping.)
- **Set CAP_NET_RAW capability (advanced):**
  ```bash
  go build -o pingcheck main.go
  sudo setcap cap_net_raw+ep ./pingcheck
  ./pingcheck -host 10.5.22.1
  ```

If you see this error, try one of the above solutions depending on your needs and environment. 