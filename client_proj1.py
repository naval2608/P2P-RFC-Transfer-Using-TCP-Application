from socket import *
import sys,os.path,os, platform, re, time, datetime

''''''''''defination list'''''''''''''''''

'''generate the add rfc message to send to server'''
def add_rfc(rfc_no,rfc_title,host,port,ver):
	protocol = "ADD RFC " + str(rfc_no) + " " + ver + "\n" + "Host: " + str(host) + "\n" + "Port: " + str(port) + "\nTitle: " + rfc_title
	#print protocol
	return protocol 

'''generate the get rfc message to send to server'''		
def get_rfclist(host,port,ver):
	protocol = "LIST ALL " + str(ver) + "\n" + "Host: " + str(host) + "\n" + "Port: " + str(port)
	return protocol

'''generate the lookup rfc message to send to server'''
def lookup_rfc(rfc_no,rfc_title,host,port,ver):
	protocol = "LOOKUP RFC " + str(rfc_no) + " " + ver + "\n" + "Host: " + str(host) + "\n" + "Port: " + str(port) + "\nTitle: " + rfc_title
        #print protocol
        return protocol

'''generate the get rfc message to send to server'''
def request_rfc(rfc_no,host,ver,os):
	protocol = "GET RFC " + str(rfc_no) + " " + ver + "\n" + "Host: " + str(host) + "\n" + "OS: " + os
	#print protocol
	return protocol

'''check the header message recieved from the client which is send along with the file'''
def check_rfc_header(msg):
	match_all = re.findall('(\w+[-]\w+[/]\d+.?\d*) (\d+) (\w+)\nDate: (.*)\nOS: (.*)\nLast-Modified: (.*)\nContent-Length: (\d+)\nContent-Type: (.*)\n(.*\s.*)+',msg)
	if match_all:
		return match_all
        else:
                return ''

'''check the header message for the rfc reply from the client'''
def check_rfc_reply(msg):
 	match_first_line = re.findall('(\w+[-]\w+[/]\d+.?\d*) (\d+) (\w+)',msg)
        if match_first_line:
		return match_first_line
	else:
		return ''

'''store the rfc no which is recieved from the client'''
def receive_rfc(clientSocket,client_dir,rfc_no):
	if os.path.exists(client_dir+"rfc"+str(rfc_no)+".txt"):
		os.remove(client_dir+"rfc"+str(rfc_no)+".txt")        
	tempFile = open(client_dir+"rfc"+str(rfc_no)+".txt", 'a')
        while 1: 
                try:
                    clientSocket.settimeout(5.0)
                    RFC_contents = clientSocket.recv(2048)
                    if not RFC_contents:
                            break
                    tempFile.write(RFC_contents)            
                except timeout:
                        break
        tempFile.close()

        temp_file = open(client_dir+"rfc"+str(rfc_no)+".txt",'r')
        file_data = temp_file.read()
        temp_file.close()
        rfc_reply_status = check_rfc_reply(file_data)
        if rfc_reply_status:
                status_code = int(rfc_reply_status[0][1])
                status_phrase = str(rfc_reply_status[0][2])
                if status_code == 200:
                        rfc_reply_details = check_rfc_header(file_data)
                        if rfc_reply_details:
                                #if valid status code then copy contents from temp file to RFC file
                                rfc_file = open(client_dir+"rfc"+str(rfc_no)+".txt")
                                readfile = rfc_file.readlines()
				header = readfile[0:6]
				for line in header:
					trim_line = str(line).strip('\n')
					print trim_line
				rfc_file.close()
                                rfc_file = open(client_dir+"rfc"+str(rfc_no)+".txt",'w')
                                rfc_file.writelines(readfile[6:])
                                rfc_file.close()
				return 1
			else:
                                rfc_file = open(client_dir+"rfc"+str(rfc_no)+".txt")
                                readfile = rfc_file.readlines()
				header = readfile[0:6]
				for line in header:
					trim_line = str(line).strip('\n')
					print trim_line
				rfc_file.close()
				os.remove(client_dir+"rfc"+str(rfc_no)+".txt")
				return -1
                else:
                        print file_data
			os.remove(client_dir+"rfc"+str(rfc_no)+".txt")
			return -1
        else:
                print file_data
		os.remove(client_dir+"rfc"+str(rfc_no)+".txt")
		return -1

'''choose peer from the list for peers which has the expected rfc'''
def choose_peer(msg):
        msg_line = msg.split('\n')
	addr_port_list = []
	
	for i in range(0, len(msg_line)):
                if i != 0:
                        #extract_host = re.findall('RFC \d+[\|][\w|\s]+[\|](.+)',msg_line[i])
			#print extract_host
			#extract_host = re.findall('(.+)[|].+[|](.+)',msg_line[i])
                        #if extract_host:
			#addr_port_list.append(str(extract_host[0][0]))
			if msg_line[i]:
				split_msg = str(msg_line[i]).split('|')
				host_ip = split_msg[2]
				host_port = split_msg[3]
				#print host_ip,host_port
				addr_port_list.append(host_ip+'|'+host_port)

                        
        print "Following are the peers that have the required RFC."
        print "SNo.|Hostname|Port"
        for i in range(0, len(addr_port_list)):
                print str(i+1)+"|"+addr_port_list[i]
                
       	peer = input("\nPlease select the serial number corresponding to the peer from which you want to download the RFC: ")
        peer_addr_port = addr_port_list[peer-1]
        return peer_addr_port


'''checks the RFC request message sent by peer'''
def check_rfc_request(msg):
        match_header = re.findall('GET RFC (\d+) (\w+[-]\w+[/]\d+.?\d*)\nHost: (\w[\w.]+).*\nOS: (.*)',msg)
        if match_header:
                return match_header
        else:
                return ''

'''set the status code of the RFC reply message based on the information collected from RFC request message'''
def set_status_code(rfc_no,request_version,client_version,client_dir,peer_name,clientname,peer_port,clientpeerport):
	if str(peer_name) == str(clientname) and (peer_port == clientpeerport):
		return 400
	elif request_version != client_version:
                return 505
        else:
                check_file = os.path.exists(client_dir+"rfc"+str(rfc_no)+".txt")
		if str(check_file) == 'False':
                        return 404
                else:
                        return 200

'''design the RFC reply message'''
def design_rfc_reply(client_ver,status,date,OS,rfc_no,client_dir,flag):        
        if flag == 1:
        #get the last modified date of file and file size in bytes
                filename = client_dir+"rfc"+str(rfc_no)+".txt"
                t = os.path.getmtime(filename)
                mdate = datetime.datetime.fromtimestamp(t)
                last_mod_date = str(mdate.strftime("%a, %d %b %Y %X"))

                content_length = os.path.getsize(filename)
                content_type = "text/plain"

                message = client_ver+" "+status+"\n"+"Date: "+date+"\n"+"OS: "+OS+"\n"+"Last-Modified: "+last_mod_date+"\n"+"Content-Length: "+str(content_length)+"\n"+"Content-Type: "+content_type+"\n"
                return message
        else:
                message = client_ver+" "+status+"\n"+"Date: "+date+"\n"+"OS: "+OS
                return message

'''Creates a new process for each client RFC request which handles the particular request'''
def handle_peer_rfc_request(clientname,clientpeerport,res,client_dir):
	try:
		clientpeerSocket = socket(AF_INET,SOCK_STREAM)
        	clientpeerSocket.bind((clientname,clientpeerport))
		clientpeerSocket.listen(5)
	except socket.error, (value,err):
        	if clientpeerSocket:
                	clientpeerSocket.close()
        	print "Could not open peer socket:" + err
        	os._exit(1)
               
        while 1:
                connectionSocket, peerAddress = clientpeerSocket.accept()
                new_process = os.fork()
                if new_process == 0:
			#print "\nnew process created:",os.getpid(),"which will handle RFC requests from: ",peerAddress
                	rfc_request = connectionSocket.recv(2048)
                        print "\n"+rfc_request

			if re.search('GET RFC .*',rfc_request):
	                	request_header = check_rfc_request(str(rfc_request))
        	        	if request_header:
					rfc_no = int(request_header[0][0])
        	                	request_version = str(request_header[0][1])
					peer_name = str(request_header[0][2])
					#print peerAddress
					peer_port = peerAddress[1]
					#print peer_port
        	                	status_code = set_status_code(rfc_no,request_version,client_ver,client_dir,peer_name,clientname,peer_port,clientpeerport)
        	        	else:
					rfc_no = 0
        	                	status_code = 400

        	        	status = str(res[status_code])

	                        #setting values for  OS and current date time
        	                #date = str(time.strftime("%a, %d %b %Y %X %Z"))
	        	        date = str(time.strftime("%a, %d %b %Y %X"))
	        	        OS = platform.system()+" "+platform.release()+" "+platform.version()

	                        #designing the RFC reply and sending it
	        	        if status_code == 200:
					rfc_reply = design_rfc_reply(client_ver,status,date,OS,rfc_no,client_dir,1)
	        	                RFCfile=open(client_dir+"/rfc"+str(rfc_no)+".txt",'r')
	        	                connectionSocket.sendall(rfc_reply + RFCfile.read())
	        	                RFCfile.close()
	        	        else:
					rfc_reply = design_rfc_reply(client_ver,status,date,OS,rfc_no,client_dir,2)   
	        	                connectionSocket.send(rfc_reply)
			else:
				connectionSocket.close()
				print "Peer " + peerAddress + " left ungracefully"
                               	print "Process " + str(os.getpid()) + " is now exiting"
				os._exit(0)
                	connectionSocket.close()
			os._exit(0)

'''Requests an RFC from peer, receives the RFC reply and processes it'''
def get_file_from_peer(peer_addr,peer_port,rfc_no,clientname,client_ver,client_os,client_dir):
        peerSocket = socket(AF_INET,SOCK_STREAM)
        #clientSocket.bind((clientname,clientport))
	peerSocket.connect((peer_addr,peer_port))
	#print "Peer connected"
        message = request_rfc(rfc_no,clientname,client_ver,client_os)
        peerSocket.send(message)
	stat = receive_rfc(peerSocket,client_dir,rfc_no)
	peerSocket.close() 	
	return stat

'''''''''''''''''Main Program'''''''''''''''
if(len(sys.argv) == 8):
	serverName = sys.argv[1]
	serverPort = int(sys.argv[2])
	clientname = sys.argv[3]
	clientport = int(sys.argv[4])
	clientpeerport = int(sys.argv[5])
	client_ver = sys.argv[6]
	client_dir = sys.argv[7]
else:
	print "Wrong set of arguments passed"
	exit(0)


#serverName = raw_input("Enter server-name:")
#serverPort = input('Enter server-port:')
#serverPort = 7734

#enter client name and port
#clientname = raw_input("Enter hostname:")
'''
while 1:
	clientport = input("Enter Portno(b/w 1025 and 65535) to connect with server:")
	if clientport >= 1025 and clientport <= 65535:
		break

while 1:
	clientpeerport = input("Enter Portno(b/w 1025 and 65535) to serve peers:")
	if clientpeerport >= 1025 and clientpeerport <= 65535:
		break


client_ver = raw_input("Enter s/w version(format P2P-CI/X.Y):")
#client_ver = 'P2P-CI/1.0'

client_dir = raw_input('Enter client directory full path:')
'''
if not os.path.exists(client_dir):
	os.makedirs(client_dir)
	print "New directory ", client_dir," has been created"

client_os = platform.system()+ " " + platform.release() + " " + platform.version()

#response list
res = {200:'200 OK',400:'400 Bad Request',404:'404 Not Found',505:'505 P2P-CI Version Not Supported'}

child_process = os.fork()
#new child process
if child_process == 0:
	#print "new process created:",os.getpid(),"which will listen for RFC requests from other clients"
	handle_peer_rfc_request(clientname,clientpeerport,res,client_dir)


#connect to the server and handle socket errors
clientSocket = socket(AF_INET,SOCK_STREAM)
clientSocket.bind((clientname,clientport))
clientSocket.connect((serverName, serverPort))

while 1:
        server_timeout = "Error!! message not received from server!!"
        server_msg = ''
	choice = input('Enter choice 1-Add RFC 2-LookUp RFC 3-List RFC 4-Exit:')
	if choice == 1:
		#inside Add rfc
		rfc_no = raw_input("Enter RFC#:")
		rfc_title = raw_input("Enter RFC Title:")
		message = add_rfc(rfc_no,rfc_title,clientname,clientpeerport,client_ver)
		clientSocket.send(message)
		while 1:
			try:
				clientSocket.settimeout(5.0)
				server_msg = clientSocket.recv(2048)
				print server_msg
			except timeout:
				if not server_msg:
					 print server_timeout
				break		
	elif choice == 2:
		'''lookup an rfc'''
		rfc_no = raw_input("Enter RFC#:")
                rfc_title = raw_input("Enter RFC Title:")
                message = lookup_rfc(rfc_no,rfc_title,clientname,clientport,client_ver)
                msg = ''
                clientSocket.send(message)
                while 1:
                        try:
                                clientSocket.settimeout(5.0)
                                server_msg = clientSocket.recv(2048)
                                #print server_msg
                                msg = msg + server_msg
                        except timeout:
				if not msg:
					print server_timeout
				break
		
		if msg:
			print msg
			rfc_reply_status = check_rfc_reply(msg)
			if rfc_reply_status:
				status_code = int(rfc_reply_status[0][1])
				status_phrase = str(rfc_reply_status[0][2])
				if status_code == 200:
					peer_addr_port = choose_peer(msg)
					peer_addr = str(peer_addr_port[:peer_addr_port.find("|")])
					peer_port = int(peer_addr_port[peer_addr_port.find("|")+1:])
					#print "Request RFC from " + peer_addr + " at port number " + str(peer_port)
					again_add_rfc = get_file_from_peer(peer_addr,peer_port,rfc_no,clientname,client_ver,client_os,client_dir)
					if again_add_rfc == 1:
						message = add_rfc(rfc_no,'NEW RFC',clientname,clientpeerport,client_ver)
				                clientSocket.send(message)
						while 1:
				                        try:
                                				clientSocket.settimeout(5.0)
				                                server_msg = clientSocket.recv(2048)
                                				print server_msg
				                        except timeout:
                                				if not server_msg:
			                                        	print server_timeout
                        					break
	elif choice == 3:
		'''list all the rfc'''
		message = get_rfclist(clientname,clientport,client_ver)
		clientSocket.send(message)
                while 1:
                        try:
                                clientSocket.settimeout(5.0)
                                server_msg = clientSocket.recv(2048)
                                print server_msg
                        except timeout:
				if not server_msg:
					print server_timeout
                                break
	elif choice == 4:
		try:
			clientSocket.send('EXIT ' + str(clientname))
			clientSocket.settimeout(5.0)	
			print "Exiting the code!!"	
			clientSocket.close()	
			break
		except timeout:
			print "Exiting the code!!"      
                        clientSocket.close()
	else:
		print "Wrong option entered, Try Again!!"
#while loop ends
os._exit(0)
