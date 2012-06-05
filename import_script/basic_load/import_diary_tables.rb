#!/usr/bin/env ruby


# Script called by data_load to read each of the
# tables that make up the diary. Does some custom 
# munging on the diary.dat table.

require 'bdb'
require 'mysql'
require 'logger'
require 'date'
require File.dirname(__FILE__) + '/import_common.rb'

# Import the diary table. Needs custom processing, as the
# key format in the existing db changed at some point from
# using the name of the event as key to using an integer.
#
# The diary entries keyed by string event name are inserted
# into old_diary, and everything else goes into diary.
def import_diary
  @log.info "Creating tables: diary, old_diary"
  @dbh.query("CREATE TEMPORARY TABLE `diary` (`datetime` VARCHAR(30) NOT NULL, `datetime_actual` DATETIME, `event_id` VARCHAR(128), PRIMARY KEY (`datetime`) )")
  # old diary has the crufty old entries from diary.dat where there isn't a numeric key, but the value is the name of the event.
  @dbh.query("CREATE TEMPORARY TABLE `old_diary` (`datetime` VARCHAR(30) NOT NULL, `datetime_actual` DATETIME, `event_id` VARCHAR(256), PRIMARY KEY (`datetime`) )")
  @log.info "Importing table: diary"

  import_from_db(@DIARY_PATH, "diary") do |key,value|
#      query_string =  "INSERT INTO `diary` VALUES('#{@dbh.escape_string(key)}','#{@dbh.escape_string( (value||"").strip )}')"
#      @dbh.query(query_string)
    # Split (datetime) key into component parts:
    actual_datetime = DateTime.strptime(key,fmt="%Y/%m/%d/%H/%M")
    # @log.info "Read " + key + " parsed to " + actual_datetime.to_s
    # Don't rely on to_i to check if things are integers, as that'll pass things like "12 nights of christmas"
    if value && value.strip =~ /^[0-9]+$/
      query_string =  "INSERT INTO `diary` VALUES('#{@dbh.escape_string(key)}','#{actual_datetime}','#{@dbh.escape_string(value.strip||"")}')"
      @dbh.query(query_string)
    else  
      query_string =  "INSERT INTO `old_diary` VALUES('#{@dbh.escape_string(key)}','#{actual_datetime}','#{@dbh.escape_string(value||"")}')"
      @dbh.query(query_string)
      # @log.error("Duff record in diary.dat: ['#{key}','#{value}']")
    end
  end
end

# import booked_by table. I forget why this is special.
def import_booked_by
  @log.info "Creating Table: booked_by"
  @dbh.query("CREATE TEMPORARY TABLE `booked_by` (`datetime` VARCHAR(30) NOT NULL, `name` VARCHAR(256), PRIMARY KEY (`datetime`) )")
  @log.info "Importing table: booked_by"
  import_from_db(@DIARY_PATH, "booked_by") do |key,value|
    query_string =  "INSERT INTO `booked_by` VALUES('#{@dbh.escape_string(key)}','#{@dbh.escape_string(value||"")}')"
    @dbh.query(query_string)
  end
end

def import_tables_diary
  import_diary
  import_booked_by
  import_boolean @DIARY_PATH,"cancelled","datetime"
  import_boolean @DIARY_PATH,"confirmed","datetime"
  import_boolean @DIARY_PATH,"discounted","datetime"
  import_boolean @DIARY_PATH,"outside_hire","datetime"
  import_boolean @DIARY_PATH,"private_event","datetime"
end
