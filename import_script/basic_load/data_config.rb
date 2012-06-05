#!/usr/bin/env ruby

require 'mysql'

@MEMBER_PATH = File.dirname(__FILE__) + "/../source_data/"
@DIARY_PATH = File.dirname(__FILE__) + "/../source_data/diary/"
@EVENTS_PATH = File.dirname(__FILE__) + "/../source_data/events/"
@EVENTS_ROLE_PATH = File.dirname(__FILE__) + "/../source_data/events/roles/"
@VOL_ROLE_PATH = File.dirname(__FILE__) + "/../source_data/roles/"

@dbh = nil

#@DATABASE_NAME = "toolkit"
@DATABASE_NAME = "toolkitimport"
@DB_USERNAME = "toolkitimport"
@DB_DANGER = "spanner"

# Open connection to toolkit_import_db. Username, server and password
# hardcoded. That should probably change.
def mysql_connect(database_name)
  begin
    @dbh = Mysql.real_connect("localhost",@DB_USERNAME,@DB_DANGER,@DATABASE_NAME)
  rescue Mysql::Error => e
    puts "Error code: #{e.errno}"
    puts "Error message: #{e.error}"
    puts "Error SQLSTATE: #{e.sqlstate}" if e.respond_to?("sqlstate")
    mysql_disconnect
  ensure
  end
end

# Close mysql connection
def mysql_disconnect
  @dbh.close if @dbh
  @dbh = nil
end
