from socket import *
import sys, os, time

##############################################################
########################  FUNCTIONS  #########################
##############################################################

# Creates and sends error response to client.
# Closes socket.
def errorResponse(statusCode, phrase):
	tnow = time.gmtime()
	tnowstr = time.strftime('%a, %d %b %Y %H:%M:%S %Z', tnow) # format time

	response = 'HTTP/1.1 ' + statusCode + ' ' + phrase + '\r\n' # status line
	response += 'Date: ' + tnowstr + '\r\n'						# header lines
	response += 'Server: Meme/4.u (Gentoo)\r\n'
	connectionSocket.send(response.encode())
	connectionSocket.close()

# Creates response with necessary header lines.
# Returns response.
def createResponse(statusCode, phrase, length, type, modified):
	tnow = time.gmtime()
	tnowstr = time.strftime('%a, %d %b %Y %H:%M:%S %Z', tnow) # format time

	response = 'HTTP/1.1 ' + statusCode + ' ' + phrase + '\r\n' # status line
	response += 'Date: ' + tnowstr + '\r\n' 					# header lines
	response += 'Server: Meme/4.u (Gentoo)\r\n'
	response += 'Last-Modified: ' + modified + '\r\n'
	response += 'Content-Length: ' + str(length) + '\r\n'
	response += 'Content-Type: ' + type + ' \r\n'
	response += '\r\n'
	return response

# Returns True if request line is properly formatted and has 
# supported Method. Sends error and returns false otherwise.
def checkRequestLine(requestLine):
	if len(requestLine) != 3:
		errorResponse('400', 'Bad Request')
		return False

	if requestLine[0] == 'BREW':
		errorResponse('418', 'I\'m a teapot')
		return False

	if requestLine[0] != 'GET':
		errorResponse('405', 'Method Not Allowed')
		return False

	if requestLine[2] != 'HTTP/1.1':
		errorResponse('505', 'HTTP Unsupported')
		return False

	return True

# Checks header lines for proper formatting and required Host
# header.  Sends error and returns false otherwise.
def checkHeaderLines(headerLines):
	# checks for last two /r/n 
	if lines[len(lines)-1] != '' or lines[len(lines)-2] != '':
		errorResponse('400', 'Bad Request')
		return False

	# searches header lines for Host
	count = 1;
	while count < len(headerLines): 
		if headerLines[count][:4] == 'Host':
			return True
		count += 1

	errorResponse('400', 'Bad Request')
	return False

# Turns time formatted in string into a time object for comparisons.
# Returns in time format.
def getTime(timeString):
	date = None
	try:
		date = time.strptime(timeString, '%a, %d %b %Y %H:%M:%S %Z')
	except ValueError:
		try:
			date = time.strptime(timeString)
		except ValueError:
			try:
				date = time.strptime(timeString, '%A, %d-%b-%y %H:%M:%S %Z')
			except ValueError:
				return None
	return date

# Gets the modified time of the file being requested.  
# Returns in string format.
def getTimeMod(file_name):
	try:
		timemod = os.path.getmtime(file_name)
	except OSError:
	    timemod = 0.0 # guarentees GET on failure

	timemod = time.gmtime(timemod)
	tmodstr = time.strftime('%a, %d %b %Y %H:%M:%S %Z', timemod)
	return tmodstr

# Compares file modified time and header if-modified time.
# Returns True if modified time was after if-modified time.
# Returns False and sends error otherwise.
def checkIfModified(headerLines, timeMod):
	count = 1;

	while count < len(headerLines):
		if headerLines[count][:6] == 'If-Mod':
			ifMod = headerLines[count][19:]

			# won't send file if modified time was before 
			# if-modified time
			if getTime(timeMod) <= getTime(ifMod):
				errorResponse('304', 'Not Modified')
				return False
			break
		count += 1

	return True

##############################################################
##########################   MAIN   ##########################
##############################################################

serverPort = int(sys.argv[1])

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(1)

print('The server is ready to recieve')

while 1:
	connectionSocket, addr = serverSocket.accept()
	
	messageBytes = connectionSocket.recv(8192)
	message = messageBytes.decode()

	length = len(message)
	if length == 0:
		print ('Zero length message')
		connectionSocket.close()
		continue

	# start parsing the HTTP request message
	lines = message.split('\r\n')

	# used for debugging from requests sent
	# for x in range(0, len(lines)):
	# 	print(lines[x])
	
	# check if Request line is valid (method, url, version)
	statusLine = lines[0].split(' ')
	if checkRequestLine(statusLine) == False:
		continue

	# check if required Header lines are present
	if checkHeaderLines(lines) == False:
		continue

	filename = statusLine[1]
	contents = ''
	timeModified = 0.0


	# distinguish between browser and not
	if filename[0] == '/':
		if len(filename) == 1:
			filename = 'index.html'
		else:
			filename = filename[1:]

	# split file into filename and extension
	fileExt = filename.split('.')
	fileType = 'text/html'

	# Try to resolve opening files by extension type.
	# Catch and error if no extension (not supported)
	try:	
		# handle text requests
		if fileExt[1] == 'txt':
			try:
				inputfile = open (filename, 'r')
				timeModified = getTimeMod(filename)

				if checkIfModified(lines, timeModified) == False:
					continue
			except IOError:
				errorResponse('404', 'File Not Found')
				continue
			contents = inputfile.read().encode()
		
		# handle .html, .htm requests
		elif fileExt[1] == 'html' or fileExt[1] == 'htm':
			fileType = 'html'
			try:
				inputfile = open (filename, 'r')
				timeModified = getTimeMod(filename)

				if checkIfModified(lines, timeModified) == False:
					continue
			except IOError:
				errorResponse('404', 'File Not Found')
				continue
			contents = inputfile.read().encode()

		# handle .jpeg, .jpg requests
		elif fileExt[1] == 'jpg' or fileExt[1] == 'jpeg':
			fileType = 'image/jpeg'
			try:
				inputfile = open(filename, 'rb')
				timeModified = getTimeMod(filename)

				if checkIfModified(lines, timeModified) == False:
					continue
			except IOError:
				errorResponse('404', 'File Not Found')
				continue
			contents = inputfile.read()

		# handle unsupported extensions
		else:
			errorResponse('415', 'Unsupported Media Type')
			continue

		# Sends generated response with 200 OK code and contents requested.
		connectionSocket.send(createResponse('200', 'OK', len(contents), fileType, timeModified).encode() + contents)
		connectionSocket.close()

	# strange separators used
	except IndexError:
		errorResponse('501', 'Not Implemented')
