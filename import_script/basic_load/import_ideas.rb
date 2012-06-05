#!/usr/bin/env ruby

require 'bdb'
require 'iconv'
require 'date'
require File.dirname(__FILE__) + '/import_common.rb'

def import_ideas(path, field_max_size = 256)
  month_names = Hash[ *( (Date::MONTHNAMES).zip((0..12).to_a) ).flatten ]

  @log.info "Creating table: ideas"
  @dbh.query("CREATE TABLE `ideas` (`date` DATETIME,`ideas` VARCHAR(#{field_max_size}), PRIMARY KEY (`date`)) ")
  @log.info "Importing table: ideas"
  table_name = "ideas"
  dupecount = 0
  count = 0

  import_from_db(path, table_name) do |key,value|    

  # Good god, I don't remember anything about Ruby :(
    date_parts = key.split("-")
    if not month_names[date_parts[0]].nil?
      query_string = "INSERT INTO `#{table_name}` VALUES('#{date_parts[1]}-#{month_names[date_parts[0]]}-1','#{@dbh.escape_string(value||"").strip}')"
      count += 1
      begin
        @dbh.query(query_string)
      rescue Mysql::Error => e
        if e.errno == 1062 #duplicate key
          @log.error("Ignoring duplicate key in table \"#{table_name}\": #{key}")
          dupecount += 1
        else
          raise $!
        end
      end
    end
  end
  if dupecount > 0 
    @log.info "Dupecount in '#{table_name}': #{dupecount}"
  end
  @log.info "Inserted #{count} into '#{table_name}'"
end
