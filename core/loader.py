import os
import sys
import inspect
import core.plugin

def load_plugins(dir, instantiate = False, shell = None):
    plugins = {}

    for root, dirs, files in os.walk(dir):
        sys.path.append(root)

        # make forward slashes on windows
        module_root = root.replace(dir, "").replace("\\", "/")

        #if (module_root.startswith("/")):
            #module_root = module_root[1:]

        #print root
        for file in files:
            if not file.endswith(".py"):
                continue

            if file in ["__init__.py"]:
                continue

            file = file.rsplit(".py", 1)[0]
            pname = module_root + "/" + file
            if (pname.startswith("/")):
                pname = pname[1:]

            if instantiate:
                if pname in sys.modules:
                    del sys.modules[pname]
                env = __import__(file, )
                for name, obj in inspect.getmembers(env):
                    if inspect.isclass(obj) and issubclass(obj, core.plugin.Plugin):
                        plugins[pname] = obj(shell)
                        break
            else:
                plugins[pname] = __import__(file)

        sys.path.remove(root)

    return plugins

def load_script(path, options = None, minimize = True):
    with open(path, "rb") as f:
        script = f.read().strip()

    #script = self.linter.prepend_stdlib(script)

    #if minimize:
        #script = self.linter.minimize_script(script)

    script = apply_options(script, options)


    return script

def apply_options(script, options = None):
    if options is not None:
        for option in options.options:
            name = "~%s~" % option.name
            val = str(option.value).encode()

            script = script.replace(name.encode(), val)
            script = script.replace(name.lower().encode(), val)

    return script

import random
import string


def random_arr_name():
	#a = "0"
	# no digits in the beginning of the name
	#while a[0] in string.digits:
	#	a = "".join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(random.randint(10,20)))
	return "z"

def split_into_chunks(script):
	#script = script.replace("\r","")
	#script = script.replace("\n","")
	#script = script.replace('\"', '\\"')
	eos = len(script)
	i = 0
	chunks = []
	while i < eos:
		randlen = random.randint(3,10)
		chunks.append(script[i:i+randlen])
		i += randlen
	#print(chunks)
	return chunks

def shuffle_chunks(chunks, name):
	num_chunks = len(chunks)
	key = list(range(0, num_chunks))
	random.shuffle(key)
	shuffled_chunks = []
	for i in key:
		shuffled_chunks.append(chunks[i])
	js_text = "var "+name+" = ["
	for c in shuffled_chunks:
		#print(c)
		js_text += "\""
		#print("".join(r'\x{0:0{1}x}'.format(ord(s), 2) for s in c))
		#js_text += c
		js_text += "".join(r'\x{0:0{1}x}'.format(ord(s), 2) for s in c)
		js_text += "\""
		#js_text += ",\r\n"
        js_text += ","

	js_text = js_text[:-1]
	js_text += "];"

	return (key, shuffled_chunks, js_text)

def rearrange_chunks(key, shuffled_chunks, name):
	chunk_len = len(key)
	i = 0
	eval_string = "eval("
	# test_string = ""
	while i < chunk_len:
		eval_string += name+"["+str(key.index(i))+"]+"
		# test_string += shuffled_chunks[key.index(i)]
		i += 1

	eval_string = eval_string[:-1]
	eval_string += ");"


	return eval_string
	# print(test_string)
