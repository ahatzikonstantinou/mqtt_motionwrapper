#!/usr/bin/env python
import paho.mqtt.client as mqtt  #import the client1
import signal   #to detect CTRL C
import sys
import requests # for communication with the cameras
import json # for publishing status

class MqttParams( object ):
    """ Holds the mqtt connection params
    """
    def __init__( self, address, port ):
        self.address = address
        self.port = port

class Camera( object ):
    """ Holds the basic params of a linux motion camera """
    def __init__( self, name, subscribeTopic, publishTopic, url, hasPanTilt, startDetection, pauseDetection, getStatus, up, down, left, right, stop ):
        self.name = name
        self.subscribeTopic = subscribeTopic
        self.publishTopic = publishTopic
        self.url = url
        self.startDetection = startDetection
        self.pauseDetection = pauseDetection
        self.getStatus = getStatus
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

    def __getAndPublishCameraStatus( self, camera ):
        status = 'UNAVAILABLE'
        #TODO
        response = __getCameraStatus( cam )
        print( response )
        self.client.publish( self.mqttParams.publishTopic, json.dumps( { 'camera': cam.name, 'status:' response } ) )

    def __on_connect( self, client, userdata, flags_dict, result ):
        """Executed when a connection with the mqtt broker has been established
        """
        #debug:
        m = "Connected flags"+str(flags_dict)+"result code " + str(result)+"client1_id  "+str(client)
        print( m )

        #subscribe to start listening for incomming commands
        for cam in self.cameras:
            self.client.subscribe( cam.subscribeTopic )
            #get the camera status and publish it
            self.__getAndPublishCameraStatus( cam )

    def __on_message( self, client, userdata, message ):
        """Executed when an mqtt arrives

        messages format: 
            "cmd": one of startDetection, pauseDetection, getStatus, up, down, left, right, stop
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
            print( '"{}" does not have the proper format i.e. \{"cmd": "one of startDetection, pauseDetection, getStatus, up, down, left, right, stop", "camera": "camera-id"\}'.format( text ) )
        for cam in cameras:
            if( cam.name == cameraName ):
                if( cmd == 'startDetection' ):
                    request.get( cam.startDetection )
                elif( cmd == 'pauseDetection' ):
                    request.get( cam.pauseDetection )
                elif( cmd == 'getStatus' ):
                    self.__getAndPublishCameraStatus( cam )
                elif( cmd == 'up' ):
                    request.get( cam.up )
                elif( cmd == 'down' ):
                    request.get( cam.down )
                elif( cmd == 'left' ):
                    request.get( cam.left )
                elif( cmd == 'left' ):
                    request.get( cam.left )
                elif( cmd == 'right' ):
                    request.get( cam.right )
                elif( cmd == 'stop' ):
                    request.get( cam.stop )
        

if( __name__ == '__main__' ):
    configurationFile = 'motionowrapper.conf'
    if( not os.path.isfile( configurationFile ) ):
        print( 'Configuration file "{}" not found, exiting.'.format( configurationFile ) )
        sys.exit()

    with open( configurationFile ) as json_file:
        configuration = json.load( json_file )
        print( 'Configuration: \n{}'.format( json.dumps( configuration, indent = 2  ) ) )
        

        motionWrapper = MotionWrapper( 
            configuration['mqttId'],
            MqttParams( configuration['mqttParams']['address'], int( configuration['mqttParams']['port'] ) ),
            [
                Camera( 
                    configuration['cameras']['name'],
                    configuration['mqttParams']['subscribeTopic'], 
                    configuration['mqttParams']['publishTopic']
                    configuration['cameras']['url'],
                    configuration['cameras']['startDetection'],
                    configuration['cameras']['pauseDetection'],
                    configuration['cameras']['status'],
                    None if configuration['cameras']['up'] is None else configuration['cameras']['up'],
                    None if configuration['cameras']['down'] is None else configuration['cameras']['down'],
                    None if configuration['cameras']['left'] is None else configuration['cameras']['left'],
                    None if configuration['cameras']['right'] is None else configuration['cameras']['right'],
                    None if configuration['cameras']['stop'] is None else configuration['cameras']['stop']
                )
                for x in configuration['cameras']
            ]
            
        )

        motionWrapper.run()