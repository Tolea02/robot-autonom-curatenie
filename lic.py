import RPi.GPIO as GPIO
import time
import serial
import threading
import cv2
import signal
import sys
import os
import numpy as np
from picamera2 import Picamera2

#pini motoare
IN1 = 27
IN2 = 17
ENA = 18

IN3 = 22
IN4 = 23
ENB = 13

#senzori
trig_front = 12
echo_front = 16
trig_right = 19
echo_right = 26
trig_left = 5
echo_left = 6

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#pin pumpa
pump_pin = 4
GPIO.setup(pump_pin, GPIO.OUT)
GPIO.output(pump_pin, GPIO.HIGH)

switch_pin = 25
GPIO.setup(switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(trig_front, GPIO.OUT)
GPIO.setup(echo_front, GPIO.IN)
GPIO.setup(trig_right, GPIO.OUT)
GPIO.setup(echo_right, GPIO.IN)
GPIO.setup(trig_left, GPIO.OUT)
GPIO.setup(echo_left, GPIO.IN)

for pin in [IN1,IN2,IN3,IN4,ENA,ENB]:
	GPIO.setup(pin, GPIO.OUT)
	GPIO.output(pin, GPIO.LOW)

pwm_ena = GPIO.PWM(ENA, 1000)
pwm_enb = GPIO.PWM(ENB, 1000)

pwm_ena.start(0)
pwm_enb.start(0)

#FUNCTII CONTROL MOTOARE
def inainte():
	global pompa_activ
	GPIO.output(IN1,GPIO.HIGH)
	GPIO.output(IN2,GPIO.LOW)
	GPIO.output(IN3,GPIO.HIGH)
	GPIO.output(IN4,GPIO.LOW)
	pwm_ena.ChangeDutyCycle(60)
	pwm_enb.ChangeDutyCycle(60)
	pompa_activ = True
	print("POMPA PORNITA")

def inapoi():
	global pompa_activ
	GPIO.output(IN1,GPIO.LOW)
	GPIO.output(IN2,GPIO.HIGH)
	GPIO.output(IN3,GPIO.LOW)
	GPIO.output(IN4,GPIO.HIGH)
	pwm_ena.ChangeDutyCycle(60)
	pwm_enb.ChangeDutyCycle(60)
	pompa_activ = False
	
def dreapta():
	global pompa_activ
	GPIO.output(IN1,GPIO.LOW)
	GPIO.output(IN2,GPIO.HIGH)
	GPIO.output(IN3,GPIO.HIGH)
	GPIO.output(IN4,GPIO.LOW)
	pwm_ena.ChangeDutyCycle(90)
	pwm_enb.ChangeDutyCycle(90)
	pompa_activ = False
	
def stanga():
	global pompa_activ
	GPIO.output(IN1,GPIO.HIGH)
	GPIO.output(IN2,GPIO.LOW)
	GPIO.output(IN3,GPIO.LOW)
	GPIO.output(IN4,GPIO.HIGH)
	pwm_ena.ChangeDutyCycle(90)
	pwm_enb.ChangeDutyCycle(90)	
	pompa_activ = False
	
def stop():
	global pompa_activ
	GPIO.output(IN1,GPIO.LOW)
	GPIO.output(IN2,GPIO.LOW)
	GPIO.output(IN3,GPIO.LOW)
	GPIO.output(IN4,GPIO.LOW)
	pwm_ena.ChangeDutyCycle(0)
	pwm_enb.ChangeDutyCycle(0)	
	pompa_activ = False
	GPIO.output(pump_pin, GPIO.HIGH)
	
def intoarcere_dreapta():
	stop()
	time.sleep(0.5)
	dreapta()
	time.sleep(1.2)
	stop()
	time.sleep(0.5)
	inainte()
	time.sleep(0.7)
	stop()
	time.sleep(0.5)
	dreapta()
	time.sleep(1.2)
	stop()
	time.sleep(0.5)
	
	
def intoarcere_stanga():
	stop()
	time.sleep(0.5)
	stanga()
	time.sleep(1.2)
	stop()
	time.sleep(0.5)
	inainte()
	time.sleep(0.7)
	stop()
	time.sleep(0.5)
	stanga()
	time.sleep(1.2)
	stop()
	time.sleep(0.5)

def ocolire_obstacol():
	stop()
	time.sleep(0.5)
					
	dreapta()
	time.sleep(0.8)
				
	stop()
	time.sleep(0.5)
					
	inainte()
	time.sleep(1.5)
					
	stop()
	time.sleep(0.5)
					
	stanga()
	time.sleep(1.6)
					
	stop()
	time.sleep(0.5)
					
	inainte()
	time.sleep(1)
					
	stop()
	time.sleep(0.5)
					
	dreapta()
	time.sleep(0.8)
	 
time.sleep(0.5)

def citeste_distanta(trig,echo):
	GPIO.output(trig,False)
	time.sleep(0.02)
	GPIO.output(trig,True)
	time.sleep(0.00001)
	GPIO.output(trig,False)
	
	t_start = time.time()
	while GPIO.input(echo) == 0:
		t_start=time.time()
	while GPIO.input(echo) == 1:
		t_stop = time.time()
	
	durata = t_stop - t_start;
	distanta = (durata*34300)/2
	return round(distanta,2)

def control_pompa():
	global ultimul_impuls, stare_pompa
	if pompa_activ:
		if time.time() - ultimul_impuls >= 0.5:
			stare_pompa = not stare_pompaGPIO.output(pump_pin, GPIO.LOW if stare_pompa else GPIO.HIGH)
			ultimul_impuls = time.time()
		else:
			GPIO.output(pump_pin, GPIO.HIGH)
			stare_pompa = False
 
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()

time.sleep(2)

ultima_intoarcere = "stanga"

try:
	print("pornit. astept switch ul sa fie pe ON")
	while True:
		if GPIO.input(switch_pin) == GPIO.LOW:
			print("mod autonom activ")
			frame = picam2.capture_array()
			df = citeste_distanta(trig_front, echo_front)
			print(f"df={df}")
			ds = citeste_distanta(trig_left, echo_left)
			print(f"ds={ds}")
			dd = citeste_distanta(trig_right, echo_right)
			print(f"dd={dd}")
			
			
			#stare 1
			if df > 20 and ((ds < 20 and dd >= 20) or (ds >= 20 and dd < 20)):
				print("stare 1: merge inainte")
				inainte()
				
			#stare 2
			elif df <= 20 and ((ds < 20 and dd >= 20) or (ds >= 20 and dd < 20)):
				frame = picam2.capture_array()
				gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
				_,thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
				contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
				if contours:
					max_cnt = max(contours, key=cv2.contourArea)
					x,y,w,h = cv2.boundingRect(max_cnt)
					cv2.rectangle(frame,(x,y), (x+w, y+h),(0,255,0),2)
						
					inaltime_img = frame.shape[0]
					latime_img = frame.shape[1]
					aria = cv2.contourArea(max_cnt)
					if w > 0.7 * latime_img and h > 0.7 * inaltime_img and aria > 5000:
						print("stare 2:robotul a ajuns in colt")
						if ds < 20:
							intoarcere_dreapta()
							ultima_intoarcere = "dreapta"
							print("dreapta")
							print("gata")
						else:
							intoarcere_stanga()
							ultima_intoarcere = "stanga"
							print("stanga")
							print("gata")
					else:
						#obstacol simplu
						print("obstacol")
						ocolire_obstacol()
				
			#stare 3+5
			elif df > 20 and ds >= 20 and dd >= 20:
				print("stare 3: liber")
				inainte()
				
			#stare 4
			elif df <= 20 and ds >= 20 and dd >= 20:
				frame = picam2.capture_array()
				gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
				_,thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
				contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
				if contours:
					max_cnt = max(contours, key=cv2.contourArea)
					x,y,w,h = cv2.boundingRect(max_cnt)
					cv2.rectangle(frame,(x,y), (x+w, y+h),(0,255,0),2)
						
					inaltime_img = frame.shape[0]
					latime_img = frame.shape[1]
					aria = cv2.contourArea(max_cnt)
					if w > 0.7 * latime_img and h > 0.7 * inaltime_img and aria > 5000:
						print("stare 4: perete fata, intoarce")	
						if ultima_intoarcere == "stanga":
							intoarcere_dreapta()
							ultima_intoarcere = "dreapta"
							print("gata")
						else:
							intoarcere_stanga()
							ultima_intoarcere = "stanga"
							print("gata")
					else:
						#obstacol simplu
						print("obstacol")
						ocolire_obstacol()
					
					
			
			#stare 6
			elif df < 20 and ds < 20 and dd < 20:
				print("blocaj complet: inapoi")
				stop()
				time.sleep(0.5)
				inapoi()
				time.sleep(1)
				intoarcere_dreapta()
				ultima_intoarcere = "dreapta"
		
		else:
			print("switch pe OFF - robot oprit")
			stop()
			time.sleep(0.5)
		control_pompa()
		time.sleep(0.5)
			
except KeyboardInterrupt:
	stop()
	picam2.stop()
	picam2.close()
	print("oprire manuala")
	GPIO.cleanup()
