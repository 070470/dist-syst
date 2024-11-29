# Server guide
## Code
The code, to be found here in the repository in three different versions (one copy for each server),
implements the client-server and inter-server message transfer as described in the architecture and
protocol specifications.

## Accessing the servers
The first step to accessing the remote virtual servers is to SSH into one of the UH 
gateway computers, such as pangolin.it.helsinki.fi, melkki.cs.helsinki.fi, melkinkari.cs.helsinki.fi or
melkinpaasi.cs.helsinki.fi. This can be done with the command `ssh pangolin.it.helsinki.fi`.
Once connected, check if you have access to the group ’grp-cs-tcpdump’ by typing in the command `group`.
If you can see the group listed in the output, you should be able to access the virtual servers.
These servers are
1. svm-11.cs.helsinki.fi
2. svm-11-2.cs.helsinki.fi
3. svm-11-3.cs.helsinki.fi,

and you can connect to them via SSH by typing in the command `ssh svm-11.cs.helsinki.fi` when logged in to the gateway computer.

The server code is located in the  `/proj` directory on each server, and the dependencies are installed in a virtual environment that is located in the same directory and should be activated with the command `source dist/bin/activate` before running the code. The transferred files will be stored in a directory named `/distfiles` on each server.

## Next steps
- ~Upload the server code & initialize the environment (install dependencies etc.) on each of the VMs~
- Make sure the code runs without error and all inter-server communications work as intended
  - The `test.py` file located on server 3 should work for testing inter-server communications, given the other servers are listening on the designated port (65411), but it hasn't been tested yet.
- Test client-server communications
