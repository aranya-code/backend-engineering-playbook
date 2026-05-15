# Nginx Notes

Created by: aranya majumdar

# Background

Nginx is a high-performance open-source web server, reverse proxy, and load balancer designed to handle massive amounts of concurrent web traffic.

It sits between client browsers and backend applications to intelligently route requests, distribute server load, and serve static content efficiently.

# Nginx Quick Study Notes

### Syntax Basics

- **Directives** -> The actual instructions or commands that tell Nginx what to do.
- **Contexts** -> Groups of related directives that apply to a certain part of the configuration.

### Performance Tuning

- **worker_processes** -> Controls how many parallel processes Nginx spawns to handle requests. It directly influences traffic handling performance and uses your CPU cores. Instead of making a new process for every single connection, it handles many connections using a single-threaded event loop.
- **worker_connections** -> The number of simultaneous connections that can be opened per worker process (default is 512).

### Server Blocks & Routing

- **Server Block** -> Defines how Nginx should handle requests for a particular domain or IP address.
- **listen** -> The IP address and port on which the server will accept requests.
server_name -> Which domain or IP address this specific server block should respond to.
- **location** -> How specific types of requests (like URLs or file types) should be handled. *Note: The root (/) URL applies to all requests unless more specific location blocks are defined*.
- **Mime.types** -> A dictionary that translates file extensions into instructions for the web browser.

### Reverse Proxy & Traffic Flow

- **proxy_pass** -> Tells Nginx to pass the request to another server, making it act as a reverse proxy. Instead of trying to find an HTML file on its own hard drive, it actively forwards the HTTP request to your backend (like Django) to let Python handle it.
- **proxy_set_header** -> Sends the actual headers from the client to the backend application (e.g., Host $host; and X-Real-IP $remote_addr;).
- **Upstream servers** -> Traffic going from a client toward the source or application server.
- **Downstream servers** -> Traffic going back to the client.

### Load Balancing

- **Upstream** -> The core of Nginx load balancing. It creates a pool of servers under one unified name (like django_cluster).

| **Algorithm** | **Best For** | **Considerations** |
| --- | --- | --- |
| **Round Robin** | Even distribution when all servers are similar. | Simple, default method, doesn't account for server load or speed. |
| **Least Connections** (`least_conn`) | Balancing load based on connection counts. | Ideal when servers handle requests at different speeds. It checks which container is working less hard and sends the new user there. |
| **IP Hash** | Session persistence (sticky sessions). | Keeps clients on the same server, but fails with server outages. |
| **Weighted Round Robin** | Servers with different capacities. | Distributes more traffic to more powerful servers. |
| **Weighted Least Connections** | Unequal server capacities, dynamic requests. | Considers both load and server strength. |