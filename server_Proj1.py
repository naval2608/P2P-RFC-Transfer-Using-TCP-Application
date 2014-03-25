from socket import *
import os
import re,sys

"'''''''''''''''Defination list''''''''''''''"

'''add peer to the peer file'''
def add_peer(file_directory,peer_list,host,uploadport,clientport):
	peer_data = str(host) + "|" +  str(clientport) + "|" + str(uploadport) + '\n'
	#print peer_data
	count = 0
	file_desc = open(file_directory + peer_list,"r")
	file_lines = file_desc.readlines()
	for line in file_lines:
		if str(line) == peer_data:
			count = 1
			break
	file_desc.close()
	if count != 1:
		file_desc = open(file_directory + peer_list,"a")
        	file_desc.write(peer_data)
        	file_desc.close()

'''handle when client exits, delete details from both rfc list and peer list'''
def client_exit(client_ad,file_dir,peer_list,rfc_list):
	'''delete peer from the peer list'''
	file_desc = open(file_dir + peer_list,"r+w")
	#print "client to delete:" + str(client_ad)
	upload_port = 0
	new_peer = []	
	data = file_desc.readlines()
	for line in data:
		match = re.findall('(.+)[|](.+)[|](.+)\n',line)
		if match:
			if match[0][0] == str(client_ad[0]) and match[0][1] == str(client_ad[1]):
				upload_port = match[0][2]			
			else:
				new_peer.append(line)
				#print str(new_peer)
	file_desc.seek(0)
	file_desc.truncate()
	file_desc.writelines(new_peer)
	file_desc.close()	
	


	'''delete rfc list for that peer'''
	file_desc = open(file_dir + rfc_list,"r")
        new_rfc = []   	
        for line in file_desc:
        	#if not re.search(str(client_ad[0]) + "|" + str(client_ad[1]),line):     
		match = re.findall('.+[|].+[|](.+)[|](.+)\n',line)
		#print match
		if match:
			if match[0][0] == client_ad[0] and match[0][1] == str(upload_port):
				'''do nothing'''
				#print "match"
			else:
	                	new_rfc.append(line)
				#print str(new_rfc)
        file_desc.close()
        #print new_rfc
        file_desc = open(file_dir + rfc_list,"w")
        file_desc.writelines(new_rfc)
        file_desc.close()	


	'''exit the child process'''
	print "Process " + str(os.getpid()) + " is now exiting"
	os._exit(0)


'''handle listall request from clients, sends details of all rfcs'''
def send_rfclist(msg,file_dir,rfc_file,res,ver,peer_list):
	match = validate_send_rfclist(msg)
	#print match
	if match:
		client_ver = match[0][0]
		host = match[0][1]
		port = match[0][2]
		if ver == client_ver:
			file_desc = open(file_dir + rfc_file,"r")
			client_msg = str(ver) + " " + str(res[200]) + "\n"
			line_msg = ''
			for line in file_desc:
				line_msg += line
				#line_msg += add_port_to_line(line,file_dir,peer_list)
			file_desc.close()
			if line_msg == '':
				return ver + " " + str(res[404])
			else:
				return str(client_msg + line_msg)
		else:
			return ver + " " + str(res[505])
	else:
		return ver + " " + str(res[400])


'''validate listall request from client'''
def validate_send_rfclist(msg):
	match = re.findall('LIST ALL (.+)\nHost: (\w[\w.]+)\nPort: (\d+)',msg)
	if match:
		return match
	else:
		return ''

'''add rfcs from client,also handle duplicate rfcs and bad request from client'''
def add_clientrfc(message,res,ver,file_directory,rfc_list,peer_list,clientaddress):
	rfc_details = validate_add_rfc(message)
        #print rfc_details
        if rfc_details:
        	rfc_no = str(rfc_details[0][0])
                client_ver = str(rfc_details[0][1])
                host = str(rfc_details[0][2])
                port = str(rfc_details[0][3])
                rfc_title = str(rfc_details[0][4])
                if client_ver == ver:
			add_peer(file_directory,peer_list,host,port,clientaddress[1])
			'''code change here'''
                	ret = add_rfc_infile(file_directory,rfc_list,host,rfc_no,rfc_title,port)
                        if ret == 1:
				send_msg = ver + " " + str(res[200]) + "\n" + rfc_no + " " + rfc_title + " " + host + " " + port
	                        #print send_msg
        	                return send_msg
			else:
				return ver + " " + str(res[400])
                else:
                        return ver + " " + str(res[505])
	else:	                                     
		 return ver + " " + str(res[400])


'''validate if the add rfc syntax is correct from the client'''
def validate_add_rfc(msg):
        #match = re.findall('ADD (RFC \d+) (.+)\n*.*Host: (\w[\w.]+).*\n*Port: (\d+).*\n*.*Title: (\w[\w\s.]+)',msg)
	match = re.findall('ADD (RFC \d+) (.+)\n*.*Host: (\w[\w.]+).*\n*Port: (\d+).*\n*.*Title: (\w.*)',msg)
        '''
        0th pattern : rfc no    1st : version   2nd : hostip    3rd : portno
        4th : title'''
        if match:
                return match
        else:
                return ''


'''add client rfc in rfc list, also checking if rfc is already present for that host'''
def add_rfc_infile(file_directory,rfc_list,host,rfc_no,rfc_title,port):
	ret = 1
	file_desc = open(file_directory + rfc_list, "r")
	if file_desc:
		for line in file_desc:
			rfc_present = re.findall('(.+)[|].+[|](.+)[|](.+)',line)
			#print rfc_present
			if rfc_present:
				'''code change here'''
				if rfc_present[0][0] == rfc_no and rfc_present[0][1] == host and rfc_present[0][2] == port:
					ret = -1
					break
			else:
				ret = -1
	file_desc.close()
	if ret == 1:
		file_desc = open(file_directory + rfc_list,"a")
	        file_desc.write(rfc_no + "|" + rfc_title + "|" + host + "|" + port + "\n")
        	file_desc.close()
	return ret


'''handle lookup request from client'''
def lookup_rfc(message,file_directory,rfc_list,res,ver,peer_list):
	rfc_details = validate_lookup_rfc(message)
	if rfc_details:
        	rfc_no = str(rfc_details[0][0])
                client_ver = str(rfc_details[0][1])
                host = str(rfc_details[0][2])
                port = str(rfc_details[0][3])
                rfc_title = str(rfc_details[0][4])
                if client_ver == ver:
			file_desc = open(file_directory + rfc_list,"r")
			send_msg = ver + " " + str(res[200]) + "\n"
			line_msg = ''
			for line in file_desc:
				extract_rfc_no = re.findall('RFC (\d+)[|](.*)\n',line)
				if extract_rfc_no:
					if int(rfc_no) == int(extract_rfc_no[0][0]):
						line_msg += line	
						#line_msg += add_port_to_line(line,file_directory,peer_list)
			file_desc.close()
			if line_msg == '':
				return ver + " " + str(res[404])
			else:
				return send_msg + line_msg
                else:
                        return ver + " " + str(res[505])	
	else:
		return ver + " " + str(res[400])

'''validate the lookup request from client'''
def validate_lookup_rfc(msg):
	#match = re.findall('LOOKUP (RFC \d+) (.+)\n*.*Host: (\w[\w.]+).*\n*Port: (\d+).*\n*.*Title: ([\w\s]+)',msg)
	match = re.findall('LOOKUP RFC (\d+) (.+)\n*.*Host: (\w[\w.]+).*\n*Port: (\d+).*\n*.*Title: (\w.*)',msg)
        '''
        0th pattern : rfc no    1st : version   2nd : hostip    3rd : portno
        4th : title'''
        if match:
                return match
        else:
                return ''

'''add port number for listall and lookup request to the rfc list file'''
def add_port_to_line(line,direc,peer_file):
	match = re.findall('.+[|].+[|](.+)\n',line)
	if match:
		ip = str(match[0])
		file_desc = open(direc + peer_file,"r")
		msg = ''
		for peer_line in file_desc:
			patt = ip + "[|](\d+)\n"
			match_port = re.findall(patt,peer_line)
			if match_port:
				port = str(match_port[0])
				msg = line.replace("\n","") + "|" + str(port) + "\n"	
		file_desc.close()
		return msg
	
	
"''''''''''''''''Main Program''''''''''''''''''''"
#server details
#serverport = 7734
#serverip = "127.1.1.1"

if(len(sys.argv) == 5):
	#serverip = raw_input("Enter server name:")
	serverip = sys.argv[1]
	serverport = int(sys.argv[2])
	#serverport = input("Enter Port to Listen:")
	#s/w version
	#ver = "P2P-CI/1.0"
	#ver = raw_input("Enter software version P2P-CI/X.Y:")
	ver = sys.argv[3]
	file_directory = sys.argv[4]
else:
	print "Wrong set of arguments passed"
	exit(0)


#response list
res = {200:'200 OK',400:'400 Bad Request',404:'404 Not Found',505:'505 P2P-CI Version Not Supported'}

#bind and listen for clients and handle exceptions
server_socket = socket(AF_INET,SOCK_STREAM)
server_socket.bind((serverip,serverport))
server_socket.listen(1)
print "Server is ready, hostname:" + serverip
print "Server process id is:",os.getpid()

#directory details to store peer and rfc list
#file_directory = "/home/naval-ubuntu/Downloads/IP_PROJ_GARGI/Server/"
#file_directory = raw_input('Enter server directory full path:')
if not os.path.exists(file_directory):
	os.makedirs(file_directory)
	print "New directory ", file_directory," has been created"
peer_list = "peer_list.txt"
rfc_list = "rfc_list.txt"
file_desc = open(file_directory + peer_list,"w").close()
file_desc = open(file_directory + rfc_list,"w").close()

while 1:
	connectionSocket, clientAddress = server_socket.accept()
	new_process = os.fork()
	#new child process
	if new_process == 0:
		print "new process created:",os.getpid(),"which will handle",clientAddress
		#add_peer(file_directory,peer_list,clientAddress)
		while 1:
			message = connectionSocket.recv(2048)
			print message
			if re.search('ADD RFC .*',message):
				'''code for adding rfc along with title, it will add the results
	       	                to the rfc_list.txt, and interpret wrong messages accordingly'''
				client_msg = add_clientrfc(message,res,ver,file_directory,rfc_list,peer_list,clientAddress)	
				connectionSocket.send(client_msg)
			elif re.search('EXIT (.*)',message):
				''' code to handle client exit, delete all data from the file belonging to this client
	                        and close the connection'''
				connectionSocket.close()
				client_exit(clientAddress,file_directory,peer_list,rfc_list)
			elif re.search('LIST ALL .*',message):
				'''send all rfc list to client'''
				client_msg = send_rfclist(message,file_directory,rfc_list,res,ver,peer_list)
				connectionSocket.send(client_msg)
			elif re.search('LOOKUP RFC .*',message):
				'''retrive hosts for the particular rfc'''
				client_msg = lookup_rfc(message,file_directory,rfc_list,res,ver,peer_list)
				connectionSocket.send(client_msg)
			else:
				#connectionSocket.send(ver + " " + str(res[400]))
				connectionSocket.close()
				print "Client " + str(clientAddress[0]) + " left ungracefully"
                                client_exit(clientAddress,file_directory,peer_list,rfc_list)	
	#child process ends
	connectionSocket.close()
