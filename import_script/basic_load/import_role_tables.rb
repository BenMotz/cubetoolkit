#!/usr/bin/env ruby

# Slightly hacky Ruby script to suck the data out of
# the various Berkelely db tables that held all the 
# old toolkit data, and load it into a bunch of spangly
# mysql tables, in a database called toolkit_import_db

require 'bdb'
require 'mysql'
require 'logger'
require File.dirname(__FILE__) + '/import_common.rb'

def import_role_table(tablename, path, merge_table, merge_key)
  @log.info "Reading role table: #{tablename}"
  import_from_db(path, tablename, "") do |key,value|
    if value.to_s.downcase == "true" then value = "1"; end
    query_string = "INSERT INTO `#{merge_table}` (`#{merge_key}`,`#{tablename}`) VALUES ('#{key}','#{value.to_i}') ON DUPLICATE KEY 
                    UPDATE `#{tablename}`='#{value.to_i}'"
    @dbh.query(query_string)
  end
end

@array_of_roles = Array.new
@array_of_volunteer_roles = Array.new

def each_table_in_dir(directory)
  tables_dir = Dir.new(directory)
  unless !tables_dir
    tables_dir.each do |filename|
      yield filename unless filename[0,1] == '.'
    end
    true
  else
    @log.error("Role directory #{directory} not found")
    false
  end
end


def import_tables_event_roles
  @dbh.query("CREATE TABLE `roles_merged` (`event_id` VARCHAR(32), PRIMARY KEY (`event_id`))")
  each_table_in_dir(@EVENTS_ROLE_PATH) { |tablename|
    query_string = "ALTER TABLE `roles_merged` ADD COLUMN `#{tablename}` INTEGER"
    @dbh.query(query_string)
  }
  each_table_in_dir(@EVENTS_ROLE_PATH) { |tablename|
    import_role_table tablename, @EVENTS_ROLE_PATH, "roles_merged", "event_id"
  }
end

def import_table_volunteer_roles
  @dbh.query("CREATE TABLE `vol_roles_merged` (`member_id` VARCHAR(32), PRIMARY KEY (`member_id`))")
  each_table_in_dir(@VOL_ROLE_PATH) { |tablename|
    query_string = "ALTER TABLE `vol_roles_merged` ADD COLUMN `#{tablename}` INTEGER"
    @dbh.query(query_string)
  }
  each_table_in_dir(@VOL_ROLE_PATH) { |tablename|
    import_role_table tablename, @VOL_ROLE_PATH, "vol_roles_merged", "member_id"
  }
end
