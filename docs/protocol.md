# The Protocol Details
The service uses two distinct ways of communication, HTTP with the client and
plain socket connection(?) between nodes.

## Server-to-server communication
The server nodes communicate between themselves when the user initiates a
download request from one of them. At this point the server nodes establish
between themselves which of them holds the most recent version of the
requested file, if any does.

Once this is established, the server serving the client will fetch the file
from another server if needed and serve it to the client.

As such, the protocol needs to support both the checking of existence and
timestamps in one call, and the request to provide data to another node in
another.

## Client-to-server-to-client communication
The client establishes connection to the server with a message following the
HTTP protocol. The server accepts `GET` and `POST` requests, and rejects all
other types with `405` status.

### GET request
On a `GET` request, the user expects to receive a file. The servers establish
which of them has the most recent file and then provide it to the client. We
respond with code `404` if no such file exists, or `200` with the requested
data if the file is found from the service.

### POST request
On a `POST` request, the user sends a file to the service. The server accepts
and stores the file, returning `204` and no further content. The servers do NOT
immediately share the file between one another, but wait for it to be requested
instead.
