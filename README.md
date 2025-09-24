# Peplink API Automation

A Python automation script for monitoring and managing Peplink router WAN connections. This tool automatically detects disconnected WAN interfaces and disables them to prevent routing issues, with optional webhook notifications.

## Features

- **WAN Monitoring**: Automatically monitors all WAN connections on your Peplink router
- **Smart Detection**: Identifies disconnected WANs and excludes passive interfaces (Wi-Fi, VLAN)
- **Auto-Disable**: Automatically disables problematic WAN connections
- **Webhook Notifications**: Sends alerts when WANs are disabled
- **System Information**: Retrieves and displays router system details
- **Secure Authentication**: Uses secure cookie-based authentication

## Prerequisites

- Python 3.12 or higher
- Access to a Peplink router with API enabled
- Network connectivity to the Peplink router

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd peplink-api
```

2. Install dependencies using uv:
```bash
uv sync
```

Or using pip:
```bash
pip install requests
```

## Configuration

Set the following environment variables:

```bash
export PEPLINK_BASE_URL="https://your-peplink-router-ip"
export PEPLINK_USERNAME="your-username"
export PEPLINK_PASSWORD="your-password"
export WEBHOOK_URL="https://your-webhook-url"  # Optional
```

### Environment Variables

- `PEPLINK_BASE_URL`: The base URL of your Peplink router (e.g., `https://192.168.1.1`)
- `PEPLINK_USERNAME`: Username for router authentication
- `PEPLINK_PASSWORD`: Password for router authentication
- `WEBHOOK_URL`: Optional webhook URL for notifications (e.g., Discord, Slack, etc.)

## Usage

Run the script:

```bash
python main.py
```

The script will:
1. Authenticate with the Peplink router
2. Retrieve system information
3. Get all WAN connection statuses
4. Check for disconnected WANs
5. Disable any problematic WANs
6. Send webhook notifications (if configured)

## WAN Status Detection

The script considers a WAN as "connected" if its status is one of:
- `Connected`
- `Connecting...`
- `Obtaining IP Address...`

Any other status is considered disconnected and will be automatically disabled.

## Passive WAN Interfaces

The following WAN interfaces are marked as passive and will not be automatically disabled:
- Wi-Fi WAN on 2.4 GHz
- Wi-Fi WAN on 5 GHz
- VLAN WAN 1

## Webhook Notifications

When a WAN is disabled, the script sends a JSON payload to the configured webhook URL:

```json
{
  "type": "WAN Disabled",
  "message": "WAN_NAME is disabled due to internet connectivity issue. The expected status should be 'Connected' but it is currently 'STATUS'."
}
```

## API Endpoints Used

The script interacts with the following Peplink API endpoints:
- `/cgi-bin/MANGA/api.cgi` - Main API endpoint
- `func=login` - Authentication
- `func=status.system.info` - System information
- `func=status.wan.connection` - WAN status
- `func=config.wan.connection.priority` - WAN configuration

## Security Notes

- The script disables SSL certificate verification for compatibility with self-signed certificates
- Authentication cookies are used for API requests
- Ensure your network is secure when using this script

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Verify your username and password
2. **Connection Refused**: Check the PEPLINK_BASE_URL and ensure the router is accessible
3. **SSL Warnings**: These are disabled by default for self-signed certificates

### Debug Output

The script provides detailed output including:
- Authentication summary
- System information
- WAN status for each interface
- Actions taken on disconnected WANs

## License

This project is open source. Please check the license file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.
