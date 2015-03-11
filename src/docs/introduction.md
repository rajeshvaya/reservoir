# Introduction

Reservoir is a distributed caching system written in Python and is based on TCP/UP sockets. Instead of the traditional memory efficient caching system, Reservoir is a smart caching system which allows numerous data types and calculations in terms of data storage and data retrieval. The communication with the Reservoir system is completely JSON based over sockets.

There are 3 client libraries (Python, PHP, NodeJS) been developed which will enable the application to communicate with the Reservoir server via sockets.
The caching system comes with out of the box replication support with multiple servers over the network and the replication is also via TCP sockets.