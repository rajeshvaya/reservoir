# Configurations

Reservoir configurations are set in the `conf/default.conf` additional custom config files can be created for specific environments like production and development. The custom conf files will be also in `conf/` folder

The configs are read and passed on to Reservoir from `Reservoir.py` and any custom confs should be also included in the SafeConfigParser


## Server configurations

### host
The address of the Reservoir cache server. To use replication make sure the host address matches the replication servers and even though multiple address may point to the single server it is best to use the uniform host address (IP / Hostname)


### port
Default port of Reserver connectivity is 3142. This can be overwritten and incase of undefined 3142 will be used by default


### max_clients
This config limits the number of connected clients to the reservoir server at any given point of time. Generally the TCP read requests would finish soon and the connection is closed in a ideal situation, however when using shell client, the connections can be limited and may affect other non-shell connections. Default value is set to 4. This can be increased depending on the server's capacity


### protocol
Reservoir caching system supports `TCP` and `UDP` protocols. Most reliable is obviously TCP and hence it is the default protocol for Reservoir caching system. Reservoir will also support HTTP in the future (Reservoir will implement a simple web server)


### max_memory_allocation
Memory usage by the Reservoir server can be limited by this config. Generally Reservoir will require a minimum of 50MB of the memory for the startup of the server. As the data is stored as smart objects rather than direct memory write the data stored will take much more memory when stored as a smart object.


### persistance
This flag will enable the cache data to be written to disk. The data will be auto reloaded in terms of crash or restart of the Reservoir server. It can be also backed up and synced to a new reservoir server instead of added the data object by object. Adding new servers with the pre-loaded data will be the most easiest thing to do with this persistant data file. The data is stored in the `data/` folder in a simple pickle file.


### persistance_interval
Setting this value will enable the persistance cycle at a particular interval. The value interpreted as seconds and since the persistance process is initiated by a child thread setting a shorter interval will not affect the performance of the caching server. 


### garbage_collection_interval
The interval at which the reservoir will start the clean up process. It will delete the expired entries from the cache. It will also delete the child cache entries for the dependants


### replication
This flag will enable or disable the replication for reservoir. `yes` is enable the replication and `no` will disable it. Changing the any of the replication flags will require a conf reload.


### replication_slave_servers
Add the slave server's host address (IP/Hostname) to the list and only then the slave server will be able to reach out to the master server. In case of the slave reservoir server this flag can be ignored, unless there is a multi-level replication. The slave will not have write permissions and can only relay the logs to its own slaves.


### replication_master_server
In case of the slave reservoir server, this flag should point to the master server's host.


### replication_sync_interval
The number of seconds after which the replication cycle will be initialized. This process will be a separate thread and will not interfere with the parent process. 


### replication_max_replay_logs
Number of replay logs to be processed with every replication cycle. 


### logger_level
The logs for reservoir server will be saved under `logs/server.log`. The logging supports INFO, DEBUG, ERROR levels. DEBUG level will output every request and response to/from the reservoir server. Note: The file can get very large and log rotation should be set as per the traffic





