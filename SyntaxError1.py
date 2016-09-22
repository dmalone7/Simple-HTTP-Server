# This is a very simple script that sends a mostly valid request,
# but with a syntax error. In this case, the word "Junk" stuck on the
# end of the request.
#
# You should make a suite of your own tests to try all the errors
# listed in the assignment checklist and any others you can think of
#
# usage: python3 SyntaxError1.py <servername> <serverport> <filename>
#  ex:   python3 SyntaxError1.py localhost 5001 test.html


from socket import *
import sys

serverName = sys.argv[1]
serverPort = int(sys.argv[2])
filename = sys.argv[3]

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))

message = 'GET ' + filename + ' HTTP/1.1 ' + 'Junk\r\n'
message += 'Host: www.cs.utexas.edu\r\n\r\n'  
clientSocket.send(message.encode())
response = clientSocket.recv(2048)
print ('From Server:' + response.decode())
clientSocket.close()
