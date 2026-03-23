An advanced desktop automation and analytics suite designed to optimize market trading in Albion Online. The application automates complex trading workflows—including flipping items to the Black Market—while synchronizing real-time price data across all users via a GCP-hosted backend.

🚀 **Key Features**

- **Market Automation**: Automates Buy Order creation, Sell Order management, and "Fast Buy" logic across all major Royal Cities and the Caerleon Black Market.

- **Global Price Synchronization**: Continuously updates an external database with the latest market scans, providing all users with up-to-date analytics and profit margins.

- **Intelligent Inventory Management**: Includes a ChestHandler to automate moving items between bank tabs, guild chests, and your inventory for efficient bulk trading.

- **Network Sniffing**: Utilizes a low-level Sniffer to capture real-time market data directly from game packets, ensuring 100% accuracy without manual input.

- **Custom Trading Presets**: Create and manage specific lists of items to track and trade based on your personal strategy.

- **Dashboard & Analytics**: Real-time visualization of order statistics and trading activity over 72-hour windows.

🛠 **Tech Stack**

- **Frontend**: Built with Flet (Python framework) for a high-performance, responsive desktop GUI.

- **Backend**: Python-based automation logic integrated with GCP (Google Cloud Platform) for data persistence and user authentication.

- **Networking**: Scapy and Pyshark for packet inspection and market data extraction.

- **OS Integration**: PyWin32 and ctypes for window management and simulated user input.

📋 **Recommended Game Settings**

For optimal bot performance, configure your Albion Online client as follows:

- **Display**: Borderless Full Screen

- **HUD Scale**: 100%

- **Window Scale**: 80%

- **Controls**: Use arrows for travel

🏗 **Project Structure**
- **/bot**: Core automation logic, including market handlers, travel logic, and the sniffer.

- **/gui**: Flet-based interface components and pages such as Dashboard, Settings, and Shop.

- **/config**: Static data including item dictionaries, location IDs, and user settings.

- **/docs**: Technical documentation and class overviews.

*Developed by Matvei Pisarev*
