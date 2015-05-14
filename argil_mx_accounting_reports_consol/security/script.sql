/*
Este script funciona en PostgreSQL 9.1, en caso de tener esta versión se recomienda sustituir en la clase account.lines
el query
*/
            drop function if exists f_account_mx_move_lines
            (x_account_id integer, x_period_id_start integer, x_period_id_stop integer);

            CREATE OR REPLACE FUNCTION f_account_mx_move_lines
            (x_account_id integer, x_period_id_start integer, x_period_id_stop integer)
            RETURNS TABLE(
            id integer,
            create_uid integer,
            create_date date,
            write_date date,
            write_uid integer,
            name varchar(64),
            move_id integer,
            user_id integer,
            journal_id integer,
            period_id integer,
            fiscalyear_id integer,
            account_id integer,
            account_type_id integer,
            move_date date,
            move_name varchar(120),
            move_ref varchar(120),
            period_name  varchar(120),
            fiscalyear_name varchar(120),
            account_code varchar(60),
            account_name varchar(120),
            account_level integer,
            account_type varchar(60),
            account_sign integer,
            journal_name varchar(60),
            initial_balance float,
            debit float, 
            credit float,
            ending_balance float) 


            AS
            $BODY$
            DECLARE
	            _cursor CURSOR FOR 
		            SELECT zx.id, zx.initial_balance, zx.debit, zx.credit, zx.ending_balance, zx.account_sign, zx.period_name, zx.move_date 
			            from hesatec_mx_auxiliar_borrame zx order by zx.period_name, zx.move_date;
	            _result record;
	            last_balance float = 0;
	            _fiscalyear_id integer;
            BEGIN

	            select fiscal.id into _fiscalyear_id
	            from account_fiscalyear fiscal where fiscal.id = (select account_period.fiscalyear_id from account_period where account_period.id = $2);

	            select 
	                case (select cast(left(account_period.name,2) as integer) from account_period where account_period.id = $2)
		            when 1 then (select account_annual_balance.initial_balance from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
		            when 2 then (select balance1 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
		            when 3 then (select balance2 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
		            when 4 then (select balance3 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
		            when 5 then (select balance4 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
		            when 6 then (select balance5 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
		            when 7 then (select balance6 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
		            when 8 then (select balance7 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
		            when 9 then (select balance8 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
		            when 10 then (select balance9 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
		            when 11 then (select balance10 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
		            when 12 then (select balance11 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
		            when 13 then (select balance12 from account_annual_balance where account_annual_balance.fiscalyear_id=_fiscalyear_id and account_annual_balance.account_id = $1)
	                end
	            into last_balance;


	            drop table if exists hesatec_mx_auxiliar_borrame;


	            create temp table hesatec_mx_auxiliar_borrame AS 
	            select move_line.id * 10000 + period.id as id, move.name as name, move.date move_date, move.name move_name, move.ref move_ref, period.name period_name, 
	            fiscalyear.name fiscalyear_name, account.code account_code, account.name account_name, account.level account_level, account_type.name account_type,  
	            account_type.sign account_sign,
	            account.id account_id, account_type.id account_type_id,
	            journal.name journal_name,
	            move.id move_id, 
	            move.create_uid user_id,
	            journal.id journal_id,
	            period.id period_id,
	            fiscalyear.id fiscalyear_id,
	            0.00::float initial_balance,
	            move_line.debit::float debit,
	            move_line.credit::float credit,
	            0.00::float ending_balance
	            from account_move move, account_move_line move_line, account_period period, account_fiscalyear fiscalyear,
	            account_account account, account_account_type account_type,  account_journal journal
	            where 
	            move.id = move_line.move_id and 
	            move_line.period_id = period.id and move_line.state='valid' and
	            fiscalyear.id = period.fiscalyear_id and
	            move_line.account_id = account.id and
	            account.user_type = account_type.id and
	            journal.id = move_line.journal_id and journal.type <> 'situation'
	            and account.id  in (select f_account_child_ids($1))
                and period.date_start >= (select _periodo1.date_start from account_period _periodo1 where _periodo1.id=$2)
		        and period.date_stop  <= (select _periodo2.date_stop from account_period _periodo2 where _periodo2.id=$3)

	            order by period.name, move.date;



	            FOR _record IN _cursor
	            LOOP
		            update hesatec_mx_auxiliar_borrame xx
		            set 	initial_balance = last_balance, 
			            ending_balance = last_balance + 
				            (xx.account_sign * (xx.debit - xx.credit))
		            where xx.id=_record.id;

		            last_balance = last_balance + (_record.account_sign * (_record.debit - _record.credit));
	            END LOOP;
	
	            return query 
		            select 	zz.id, zz.user_id create_uid, current_date create_date, current_date write_date, 
			            zz.user_id write_uid, zz.name, zz.move_id, zz.user_id, zz.journal_id, zz.period_id, zz.fiscalyear_id,
			            zz.account_id, zz.account_type_id, zz.move_date, zz.move_name, zz.move_ref, 
			            zz.period_name, 
			            zz.fiscalyear_name, zz.account_code, zz.account_name, zz.account_level,	zz.account_type, 
			            zz.account_sign, zz.journal_name, 
			            zz.initial_balance, zz.debit, zz.credit, zz.ending_balance
		            from hesatec_mx_auxiliar_borrame zz
		            order by period_name, move_date, account_code;


            END
            $BODY$
            LANGUAGE 'plpgsql' ;

