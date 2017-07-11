#!/usr/bin/env python
import paho.mqtt.client as mqtt  #import the client1
import signal   #to detect CTRL C
import sys
import os
import requests # for communication with the cameras
import json # for publishing status

class MqttParams( object ):
    """ Holds the mqtt connection params
    """
    def __init__( self, address, port, subscribeTopic, publishTopic ):
        self.address = address
        self.port = port
        self.subscribeTopic = subscribeTopic
        self.publishTopic = publishTopic

class Camera( object ):
    """ Holds the basic params of a linux motion camera """
    def __init__( self, name, url, startDetection, pauseDetection, getState, up, down, left, right, stop ):
        self.name = name
        self.url = url
        self.startDetection = startDetection
        self.pauseDetection = pauseDetection
        self.getState = getState
        self.up = up
        self.down = down
        self.left = left
        self.right = right
        self.stop = stop
        self.hasPanTilt = self.up is not None and self.down is not None and self.left is not None and self.right is not None and self.stop

class MotionWrapper( object ):
    """ This class proxys the linux motion program which does motion detection 
    """
    def __init__( self, mqttId, mqttParams, cameras ):
        self.mqttParams = mqttParams
        self.mqttId = mqttId
        self.cameras = cameras
        signal.signal( signal.SIGINT, self.__signalHandler )

    def run( self ):
        #create a mqtt client
        self.client = mqtt.Client( self.mqttId )
        self.client.on_connect = self.__on_connect
        self.client.on_message = self.__on_message
        #set last will and testament before connecting
        self.client.will_set( self.mqttParams.publishTopic, json.dumps({ 'main': 'UNAVAILABLE' }), qos = 1, retain = True )
        self.client.connect( self.mqttParams.address, self.mqttParams.port )
        self.client.loop_start()
        #go in infinite loop
        while( True ):
            pass

    def __signalHandler( self, signal, frame ):
        print('Ctrl+C pressed!')
        self.client.disconnect()
        self.client.loop_stop()
        sys.exit(0)        

    def __getAndPublishCameraState( self, camera ):
        state = 'UNAVAILABLE'
        try:
            response = requests.get( camera.getState ).text
            print( response )
            state = 'ACTIVE' if 'status ACTIVE' in response else 'PAUSED'
        except:
            pass
        self.client.publish( self.mqttParams.publishTopic, json.dumps( { 'camera': camera.name, 'state': state } ), qos = 2, retain = True )

    def __on_connect( self, client, userdata, flags_dict, result ):
        """Executed when a connection with the mqtt broker has been established
        """
        #debug:
        m = "Connected flags"+str(flags_dict)+"result code " + str(result)+"client1_id  "+str(client)
        print( m )

        self.client.publish( self.mqttParams.publishTopic, json.dumps({ 'main': 'AVAILABLE' }), qos = 1, retain = True )
        #subscribe to start listening for incomming commands
        self.client.subscribe( self.mqttParams.subscribeTopic )

        for cam in self.cameras:
            #get the camera status and publish it
            self.__getAndPublishCameraState( cam )

    def __on_message( self, client, userdata, message ):
        """Executed when an mqtt arrives

        messages format: 
            "cmd": one of startDetection, pauseDetection, getState, up, down, left, right, stop
            "camera": name of the camera e.g. 1, or 2, or ...
        """
        text = message.payload.decode( "utf-8" )
        print( 'Received message "{}"'.format( text ).encode( 'utf-8' ) )
        if( mqtt.topic_matches_sub( self.mqttParams.subscribeTopic, message.topic ) ):
            try:
                jsonMessage = json.loads( text )
            except ValueError, e:
                print( '"{}" is not a valid json text, exiting.'.format( text ) )
                return

        try:
            cmd = jsonMessage[ 'cmd' ]
            cameraName = jsonMessage[ 'camera' ]
        except:
            print( '"{}" does not have the proper format i.e. \{"cmd": "one of startDetection, pauseDetection, getState, up, down, left, right, stop", "camera": "camera-id"\}'.format( text ) )
        for cam in self.cameras:
            if( cam.name == cameraName ):
                print( 'Found camera name "{}" will execute command "{}"'.format( cameraName, cmd ) )
                try:
                    if( cmd == 'startDetection' ):
                        requests.get( cam.startDetection )
                        self.__getAndPublishCameraState( cam )
                    elif( cmd == 'pauseDetection' ):
                        requests.get( cam.pauseDetection )
                        self.__getAndPublishCameraState( cam )
                    elif( cmd == 'getState' ):
                        self.__getAndPublishCameraState( cam )
                    elif( cmd == 'up' ):
                        requests.get( cam.up )
                    elif( cmd == 'down' ):
                        requests.get( cam.down )
                    elif( cmd == 'left' ):
                        print( 'Sending cmd left to "{}"'.format( cam.left ) )
                        requests.get( cam.left )
                    elif( cmd == 'left' ):
                        requests.get( cam.left )
                    elif( cmd == 'right' ):
                        requests.get( cam.right )
                    elif( cmd == 'stop' ):
                        requests.get( cam.stop )
                except Exception, e:
                    print e.message
        

if( __name__ == '__main__' ):
    configurationFile = 'motionwrapper.conf'
    if( not os.path.isfile( configurationFile ) ):
        print( 'Configuration file "{}" not found, exiting.'.format( configurationFile ) )
        sys.exit()

    with open( configurationFile ) as json_file:
        configuration = json.load( json_file )
        print( 'Configuration: \n{}'.format( json.dumps( configuration, indent = 2  ) ) )
        

        motionWrapper = MotionWrapper( 
            configuration['mqttId'],
            MqttParams( configuration['mqttParams']['address'], int( configuration['mqttParams']['port'] ), configuration['mqttParams']['subscribeTopic'], configuration['mqttParams']['publishTopic'] ),
            [
                Camera( 
                    x['name'],
                    x['url'],
                    x['startDetection'],
                    x['pauseDetection'],
                    x['state'],
                    None if x['up'] is None else x['up'],
                    None if x['down'] is None else x['down'],
                    None if x['left'] is None else x['left'],
                    None if x['right'] is None else x['right'],
                    None if x['stop'] is None else x['stop']
                )
                for x in configuration['cameras']
            ]
            
        )

        motionWrapper.run()