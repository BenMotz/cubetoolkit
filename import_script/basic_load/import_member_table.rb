#!/usr/bin/env ruby
#name|email|homepage|address|city|postcode|country|landline|mobile|last updated|refuse mailshot|status
#0    1     2        3       4    5        6       7        8      9            10              11

# if status ~= volunteer then, err, well...

require 'bdb'
require 'mysql'
require 'logger'
require File.dirname(__FILE__) + '/import_common.rb'


def import_table_member
  @log.info "Creating table: members"
  @dbh.query("CREATE TABLE `members` (`member_id` VARCHAR(128) NOT NULL,
                                      `name` VARCHAR(256),
                                      `email` VARCHAR(256),
                                      `homepage` VARCHAR(256),
                                      `address` VARCHAR(256),
                                      `city` VARCHAR(256),
                                      `postcode` VARCHAR(256),
                                      `country` VARCHAR(256),
                                      `landline` VARCHAR(256),
                                      `mobile` VARCHAR(256),
                                      `last_updated` VARCHAR(256),
                                      `refuse_mailshot` VARCHAR(256),
                                      `status` VARCHAR(256), PRIMARY KEY(`member_id`) )")

  @log.info "Importing table: members"
  count = 0
  dupecount = 0

  import_from_db(@MEMBER_PATH, "members") do |key,value|
    #Check key is neither null nor contains non numeric characters:
    if (key == nil || !(key.strip =~ /^[0-9]+$/) )
      @log.error "Member has deeply suspect key: #{key}"
    else # if key is valid:  
      fields = value.split('|')

      # Force the array to have 12 elements, if it didn't already.
      if fields[11] == nil then fields[11]=""; end

      query_string = "INSERT INTO `members` VALUES('#{@dbh.escape_string(key.to_s.strip)}'"

      fields.each { |string|
        query_string += ",'#{@dbh.escape_string(string.to_s.strip)}'"
      }
      query_string += ")"
      count += 1

      #Give a vague idea of progress:
      if (count % 500) == 0
        print "."
        STDOUT.flush
      end

      begin
        @dbh.query(query_string)
      rescue Mysql::Error => e
        if e.errno == 1062 #duplicate key
          @log.error("Ignoring duplicate key in table 'member': #{key}, fields #{fields}")
          dupecount += 1
        else
          raise $!
        end
      end
    end
  end
  puts
  @log.info "Inserted #{count} into 'members'"
end
