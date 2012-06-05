#!/usr/bin/env ruby

# Script called by data_load to read all the tables
# concerning events. Rather simple, really.

require 'bdb'
require 'mysql'
require 'logger'
require File.dirname(__FILE__) + '/import_common.rb'

def import_tables_events
  import_strings @EVENTS_PATH,"copy","event_id", false, 4096
  import_strings @EVENTS_PATH,"copy_summary","event_id", false, 4096
  import_strings @EVENTS_PATH,"event_name","event_id", false, 512
  import_strings @EVENTS_PATH,"image_credits","event_id"
  import_strings @EVENTS_PATH,"duration","event_id"
  import_strings @EVENTS_PATH,"terms","event_id", false, 4096
end

