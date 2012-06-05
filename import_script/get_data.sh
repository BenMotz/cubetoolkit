#!/bin/bash
# Not very profound, this one.

SERVER="sparror.cubecinema.com"
USER="cube"
RSYNC="/usr/bin/rsync"

DIARY_SERVER_PATH="/home/cube/cgi-bin/diary/data"
DIARY_LOCAL_PATH="./source_data/diary"

EVENTS_SERVER_PATH="/home/cube/cgi-bin/events/data"
EVENTS_LOCAL_PATH="./source_data/events"

MEMBERS_SERVER_FILE="/home/cube/cgi-bin/members/members.dat"
MEMBERS_LOCAL_PATH="./source_data/"

VOLUNTEERS_SERVER_FILE="/home/cube/cgi-bin/volunteers/notes/notes.dat"
VOLUNTEERS_LOCAL_PATH="./source_data/"

ROLES_SERVER_PATH="/home/cube/cgi-bin/volunteers/roles/"
ROLES_LOCAL_PATH="./source_data/roles/"

EVENT_PHOTO_SERVER_PATH="/home/cube/htdocs/events/images/"
EVENT_PHOTO_LOCAL_PATH="./source_data/media/events/"

VOL_PHOTO_SERVER_PATH="/home/cube/htdocs/volunteers/portraits/"
VOL_PHOTO_LOCAL_PATH="./source_data/media/portraits/"

echo "Getting Diary"
$RSYNC -av --exclude='.svn' $USER@$SERVER:$DIARY_SERVER_PATH/*.dat $DIARY_LOCAL_PATH/
echo "Getting Events"
$RSYNC -av --exclude='.svn' $USER@$SERVER:$EVENTS_SERVER_PATH/*.dat $EVENTS_LOCAL_PATH/
echo "Getting Event roles"
$RSYNC -av --exclude='.svn' $USER@$SERVER:$EVENTS_SERVER_PATH/roles/* $EVENTS_LOCAL_PATH/roles/

echo "Getting Members"
$RSYNC -av --exclude='.svn' $USER@$SERVER:$MEMBERS_SERVER_FILE $MEMBERS_LOCAL_PATH
echo "Getting Volunteer notes"
$RSYNC -av --exclude='.svn' $USER@$SERVER:$VOLUNTEERS_SERVER_FILE $VOLUNTEERS_LOCAL_PATH
echo "Getting Volunteer roles"
$RSYNC -av --exclude='.svn' $USER@$SERVER:$ROLES_SERVER_PATH/ $ROLES_LOCAL_PATH/
echo "Getting Volunteer photos"
$RSYNC -av --exclude='.svn' --progress $USER@$SERVER:$VOL_PHOTO_SERVER_PATH $VOL_PHOTO_LOCAL_PATH
echo "Getting Event photos"
$RSYNC -av --exclude='.svn' --progress $USER@$SERVER:$EVENT_PHOTO_SERVER_PATH $EVENT_PHOTO_LOCAL_PATH

exit 0
