--require("png") --https://github.com/DelusionalLogic/pngLua

--terminal komandoak exekutatzeko
function os.capture(cmd, raw) 
  local f = assert(io.popen(cmd, 'r'))
  local s = assert(f:read('*a'))
  f:close()
  if raw then return s end
  s = string.gsub(s, '^%s+', '')
  s = string.gsub(s, '%s+$', '')
  s = string.gsub(s, '[\n\r]+', ' ')
  return s
end


--Windows-en CMD bidez irudia lortzeko, oso geldoa
function getImagePipe()

	client.screenshottoclipboard()
	local cmd = ("python .\\clipboardimage.py")

	local image = os.capture(cmd)
	return image
end

--irudia png moduan gorde eta kargatu
function getImage()
	image = ""
	client.screenshot("frame.png")
	img = pngImage("frame.png", newRowCallback)

	return image
end


--socket bidezko komunikazioa
function getSocket()
	comm.socketServerSetTimeout(1000)
	response = comm.socketServerScreenShotResponse()
	return response
end

--http bidezko komunikazioa
function getHttp(postreq)
	client.screenshottoclipboard()
	image = comm.httpPost("http://192.168.0.18:8081",postreq)
	return image
end