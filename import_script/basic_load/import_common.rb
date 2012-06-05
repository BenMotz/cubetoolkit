#!/usr/bin/env ruby


# A few handy methods called by other scripts. One method
# to handle opening berkeley db files and process each key/value pair
# Another to import a table of true/false, and store it in a table 
# with a boolean data type, and another (pretty evil) to just store
# all the values straight in a field, as strings.

require 'bdb'
require 'iconv'
# General purpose function to import all the key/value pairs
# from a berkeley db file. Assumes a single database in the file.
# Reads the file at path/table_name.dat and calls the block
# with each key/value pair.
def import_from_db(path, table_name, file_extension = ".dat")
  @dbh.query("START TRANSACTION")
  db = BDB::Hash.open path+table_name+file_extension,nil, BDB::RDONLY
  db.each_pair do |key,value|
    #   key_coded =  Iconv.iconv("Windows-1252","utf8",key)
    #   value_coded = Iconv.iconv("Windows-1252","utf8",value)
    #Shove through iconv to catch any stupid unicode
    begin
      key_coded =  Iconv.iconv("utf8","Windows-1252",key).to_s
      value_coded = Iconv.iconv("utf8","Windows-1252",value).to_s
    rescue Iconv::IllegalSequence
      50.times { putc "=" }
      puts "\nHideously broken at\nKey: #{key}\nValue: #{value}"
      50.times { putc "=" }
      puts "\nWill insert crap instead\nPressenter"
      gets
      value_coded = "[Error processing]"
    end
    yield key_coded, value_coded
  end
  db.close
  @dbh.query("COMMIT")
end

# General purpose method to read boolean data from berkeley file
# at path/table_name.dat into mysql table `table_name`
# with the keys going into a column key_name, and the (boolean) values 
# going into a column table_name. (Creates the table first)
def import_boolean(path, table_name, key_name, file_extension = ".dat")
  @log.info "Creating table: #{table_name} [key: #{key_name}]"
  @dbh.query("CREATE TEMPORARY TABLE `#{table_name}` (`#{key_name}` VARCHAR(30) NOT NULL, `#{table_name}` BOOLEAN, PRIMARY KEY (`#{key_name}`) )")

  @log.info "Importing table: " + table_name
  import_from_db(path, table_name, file_extension) do |key,value|
    query_string = "INSERT INTO `#{table_name}` VALUES('#{@dbh.escape_string(key)}','#{ ((value||"") == "true") ? '1' : '0' }')"
    @dbh.query(query_string)
  end
end

# General purpose method to read string data from berkeley file
# at path/table_name.dat into mysql table `table_name`
# with the keys going into a column called `datetime`, and the
# values going into a column table_name. Ignores any rows with
# duplicate keys
def import_strings(path, table_name, primary_key_name, not_temporary = false, field_max_size = 256)
  @log.info "Creating table: #{table_name} [key: #{primary_key_name}]"
  @dbh.query("CREATE #{ not_temporary ? "" :"TEMPORARY" } TABLE `#{table_name}` (`#{primary_key_name}` VARCHAR(128),`#{table_name}` VARCHAR(#{field_max_size}), PRIMARY KEY (`#{primary_key_name}`) )")

  @log.info "Importing table: " + table_name
  dupecount = 0
  count = 0
  import_from_db(path, table_name) do |key,value|    
    query_string = "INSERT INTO `#{table_name}` VALUES('#{@dbh.escape_string(key.to_s.strip)}','#{@dbh.escape_string(value||"").strip}')"
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
  if dupecount > 0 
    @log.info "Dupecount in '#{table_name}': #{dupecount}"
  end
  @log.info "Inserted #{count} into '#{table_name}'"
end
