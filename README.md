# 📸 SnapSpan

One click, all screens, unified

## Features

- Capture screenshots from multiple monitors
- Scale up images to match the highest resolution
- Stitch images together
- Save screenshots with optimization and compression
- Detect changes between consecutive screenshots
- Schedule screenshot captures at regular intervals (every 60 seconds)

## Usage

1. Run the application using `python main.py`
2. Click on the menu bar icon to access scheduling options
3. Choose from "Start Scheduling" or "Stop Scheduling"
4. Select the interval for scheduled screenshot captures (default: 60 seconds)

## Requirements

- Python 3.x

- To set up your environment, run `make deps`. 
This command will install all required dependencies using pip. 
If you need to upgrade any of these dependencies, simply re-run this command.

## Building the package

To build the SnapSpan package, run `make package`. 
This will create a tarball of the project in the `dist` directory.

## Contributing

Contributions are welcome! Please create a new issue to discuss changes or propose new features.

## License

SnapSpan is released under the MIT License.
