

require "pipe"

local ram = "RAM"
local nametable = "CIRAM (nametables)"



levelselect = 3

local function print(string)
	console.writeline(string)
end

local function getScore()
	local marioXw = memory.readbyte(0x0086,ram) 		
	local marioXscreen = memory.readbyte(0x006D,ram)
	return marioXw+ 256*marioXscreen;
end


local function updateState(postreq, override)
	local response = getHttp(postreq)
	if override then
		NNaction = tonumber(response)
	end
end


local function int2action(integer)
	if integer <0 or integer > 3 then
		integer = 2
	end
	action = {}
	if integer == 0 then
		action["P1 A"]="True"
		action["P1 Right"]="False"
		action["P1 B"]="False"
		lastAction = 0
	elseif integer == 1 then
		action["P1 A"]="False"
		action["P1 Right"]="True"
		action["P1 B"]="False"
		lastAction = 1
	elseif integer == 2 then
		action["P1 Right"]="True"
		action["P1 B"]="True"
		action["P1 A"]="True"
		lastAction = 2
	elseif integer == 3 then
		action["P1 A"]="False"
		action["P1 Right"]="True"
		action["P1 B"]="True"
		lastAction = 3
	elseif integer == 4 then
		action["P1 Left"]="True"
		action["P1 B"]="True"
		lastAction = 4
	elseif integer ==5 then
		action["P1 Left"]="True"
		action["P1 B"]="True"
		action["P1 A"]="True"
		lastAction = 5
	elseif integer ==6 then
		action["P1 Left"]="True"
		lastAction = 6

	end

end




local function reset()
	
	--updateQtable(true) --terminal state,  update qtable

	deathcount = deathcount + 1
	framecount = 0
	rst = false

	savestate.loadslot(levelselect)

end


local function 	checkLevelCleared()
	local flag = memory.readbyte(0x001D,ram)
	local cleared = false
	if flag == 3 then
		levelcleared = true
		cleared = true
		rst = true
	end

	if levelcleared then
		endtime = os.time()
		elapsedtime = endtime - starttime
		console.writeline("Level cleared. Total deaths: "..deathcount..". Elapsed time: "..elapsedtime.." seconds.")
		levelcleared = false
	end
	return cleared


end

local function checkReset()
	rst = false

	mariostate = memory.readbyte(0x000E,ram) --killed by enemy
	if(mariostate == 0x06 or mariostate == 0x0B) then
		rst = true

	end
	marioyscreen = memory.readbyte(0x00B5,ram) --zulotik behera
	if marioyscreen>1 then
		rst = true
	end
	return rst
end


console.writeline("Starting")
savestate.loadslot(levelselect)
action = ""
lastscore = 0
deathcount = 0
levelcleared = false
starttime = os.time()
framecount = 0
clearedgame = false
resetgame = false

useframecount = 4
NNaction = -1



----[[
while true do
	emu.frameadvance();
	framecount = framecount + 1
	
	if not(framecount % useframecount == 0) then
		updateState("{'process':'0'}", false)
	end

	if framecount % useframecount == 0 then

		resetgame = checkReset()
		clearedgame = checkLevelCleared()
	

		--console.writeline("currentscore: "..getScore().." lastscore: "..lastscore)
		

		stepscore = getScore()-lastscore
		--console.writeline("score: "..stepscore)
		if(resetlastscore) then
			stepscore = 0
			resetlastscore = false
		end
		--json request
		post = "{ 'process':'1' "
		post = post .. ", 'score':'" .. stepscore .."'"
		if resetgame or clearedgame then
			resetlastscore = true --hurrengo egoera hasierakoa izango da, beraz saria = 0
			post = post .. ",'terminal':'1'"
		else 
			post = post .. ",'terminal':'0'"
		end
		if clearedgame then
			post = post .. ",'cleared':'1'"
		else
			post = post .. ",'cleared':'0'"
		end
		post = post .. "}"

		
		updateState(post, true)
		
		if rst then
			reset()
		end

		lastscore = getScore()

		if NNaction ~= nil and NNaction >= 0 then
			int2action(NNaction)
		end
	end
	--print(action)
	if action ~= "" then
		joypad.set(action)
	end

end
--]]