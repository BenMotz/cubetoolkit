#!/usr/bin/env ruby1.8

# Very hacky Ruby script to suck the data out of
# the various Berkelely db tables that held all the 
# old toolkit data, and load it into a bunch of slightly 
# spangly mysql tables, in a database called toolkit_import_db

require 'bdb'
require 'mysql'
require 'logger'
require 'iconv'
require File.dirname(__FILE__) + '/data_config.rb'

require File.dirname(__FILE__) + '/import_event_tables.rb'
require File.dirname(__FILE__) + '/import_diary_tables.rb'
require File.dirname(__FILE__) + '/import_role_tables.rb'
require File.dirname(__FILE__) + '/import_member_table.rb'
require File.dirname(__FILE__) + '/consolidate_tables.rb'
require File.dirname(__FILE__) + '/import_ideas.rb'

@log = Logger.new(STDOUT)

def drop_database
  @log.info "Dropping database #{@DATABASE_NAME}"
  @dbh.query "DROP DATABASE IF EXISTS #{@DATABASE_NAME}"
end
def create_database
  @log.info "Creating database #{@DATABASE_NAME}"
  @dbh.query "CREATE DATABASE #{@DATABASE_NAME}  CHARACTER SET 'utf8'"
end

mysql_connect "mysql"

if @dbh
  drop_database
  create_database
  mysql_disconnect
  mysql_connect @DATABASE_NAME

  import_tables_diary
  import_tables_events
  import_tables_event_roles
  import_table_volunteer_roles

  # import the hacky, hacky members database:
  import_table_member
  # import the notes associated with members who're volunteers
  import_strings @MEMBER_PATH,"notes","member_id", true, 1024
  # import the monthly ideas table
  #import_strings @EVENTS_PATH,"ideas","month_year",true, 4096
  import_ideas @EVENTS_PATH, 4096

  #Hacky step. See method definition for explanation.
  create_old_diary_event_names

  merge_tables_diary
  merge_tables_old_diary
  merge_tables_events

  rename_tables

  mysql_disconnect
  @log.info "Done."
else
  puts "Failed to connect to database"
end
