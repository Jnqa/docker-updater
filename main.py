# -*- coding: utf-8 -*-
import os
import subprocess
import telebot
from telebot import types

try:
    botToken = os.environ['botToken']
    hostKey = os.environ['hostKey']
    hostIP = os.environ['hostIP']
    hostUser = os.environ['hostUser']
except:
    print("where is my keys?")

class HostController:
    def __init__(self, hostIP, hostUser, hostKey):
        self.hostIP = hostIP
        self.hostUser = hostUser
        self.hostKey = hostKey
        self.containers = self.get_container_info()

    def run_command(self, command):
        return subprocess.check_output(
            f"sshpass -p {self.hostKey} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=sshfile {self.hostUser}@{self.hostIP} {command}",
            shell=True).decode("utf-8")

    def get_container_info(self):
        containers = {}
        try:
            names = list(filter(None, self.run_command("docker ps --format '{{.Names}}'").split("\n")))
            images = list(filter(None, self.run_command("docker ps --format '{{.Image}}'").split("\n")))
            for n in names:
                containers[n] = images[names.index(n)]
        except Exception as error:
            print(f"ERROR: {error}")
        return containers

    def get_ports(self, contanierName):
        ports = self.run_command(f"docker port {contanierName}")
        portIN = ports.split("\n")[0].split("/")[0]
        portOUT = ports.split("\n")[0].split(":")[1]
        return [portIN, portOUT]


    def upgrade_container(self, contanierName):
        status = self.run_command(f"docker pull {self.containers[contanierName]}")
        ports = self.get_ports(contanierName)
        print(f"Ports: {ports}")
        if "Status: Image is up to date" in status:
            return False
        else:
            next = self.run_command(f'docker stop {contanierName}')
            print(next)
            next = self.run_command(f'docker rm {contanierName}')
            print(next)
            next = self.run_command(f'docker run --name={contanierName} --restart=always -d -p {ports[1]}:{ports[0]} {self.containers[contanierName]}')
            print(next)
            return True



tbot = telebot.TeleBot(botToken, None)
Controller = HostController(hostIP, hostUser, hostKey)
print(Controller.containers)
# print(Controller.upgrade_container('lk-weather'))

@tbot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    cb_first = str(call.data).split(" ")[0]
    cb_second = str(call.data).split(" ")[1]
    if cb_first == "upgrade":
        tbot.answer_callback_query(call.id, f"☝🏻 Запущено обновление {cb_second}",
                                   show_alert=False)
        if Controller.upgrade_container(cb_second):
            msg_text = f"🔄 Обновляю {cb_second}..."
        else:
            msg_text = f"✅ Нет новой версии для {cb_second}"
        tbot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                               text=msg_text, parse_mode='html')


@tbot.message_handler(commands=['containers'])
def containers(message):
    containers = Controller.containers
    markup = types.InlineKeyboardMarkup()
    msg = f"Выбери контейнер:"
    for k, v in containers.items():
        if k != 'docker-controller':
            markup.add(types.InlineKeyboardButton(f"🐳 {k}", callback_data=f"upgrade {k}"))
    tbot.send_message(message.chat.id, text=msg, reply_markup=markup, parse_mode='html')


tbot.polling(none_stop=True)
