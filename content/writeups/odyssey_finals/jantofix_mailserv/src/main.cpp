#include <iostream>
#include <string.h>
#include <vector>
#include <sstream>
#include <unistd.h>
#include <stdint.h>

class srv_exception : public std::exception {
	private:
		std::string message;

	public:
		srv_exception(const char* msg): message(msg){}
		const char* what() const throw() {
			return message.c_str();
		}
};

class Mail {
	public :
		std::string	sender;
		std::string	receiver;
		char		data[1024];
		uint16_t	dsize = 1024;
		bool		sent = false;
};
uint64_t		users_c = 0;

class User {
	public :
		uint64_t		id = 0;
		std::string		fname;
		std::string		lname;
		std::string		password;
		std::string		email_handle;
		std::vector<Mail>	inbox;
		User(std::string fname,std::string lname, std::string password, std::string email_handle){
			this->fname = fname;
			this->lname = lname;
			this->password = password;
			this->email_handle = email_handle;
			this->id = users_c;
		}
};

User	*users[1024];
Mail	current_mail;

void  __attribute__((constructor)) ignore_me(){
        setvbuf(stdin, 0, _IONBF, 0);
        setvbuf(stdout, 0, _IONBF, 0);
        setvbuf(stderr, 0, _IONBF, 0);
	srand(time(0));
        alarm(128);
}

std::vector<std::string> split_cmd(std::string cmd, char delim){
	std::stringstream scmd(cmd);
	std::vector<std::string> splcmd;
	std::string pcmd;
	while (std::getline(scmd, pcmd, delim)){
		splcmd.push_back(pcmd);
	}
	return (splcmd);
}

void create_user(std::vector<std::string> splcmd){
	// syntax AUTH <fname> <lname> <password> <email_handle>
	if (splcmd.size() != 5){
		throw srv_exception("555 Bad syntax");
		return ;
	}
	if (users_c > 1000){
		throw srv_exception("555 max account limit is reached");
	}
	User *nuser = new User(splcmd[1], splcmd[2], splcmd[3], splcmd[4]);
	users[users_c] = nuser;
	users_c++;
	throw srv_exception("235 Ok");
}

void verify_user(std::vector<std::string> splcmd){
	// syntax : VRFY handle <email_handle>
	// syntax : VRFY id <user_id>
	if (splcmd.size() < 3){
		throw srv_exception("555 Bad syntax");
	}
	if (splcmd[1] == "handle"){
		uint16_t i = 0;
		while (i < users_c){
			if ((users[i])->email_handle == splcmd[2]){
				std::cout << "250 "  << "[" << users[i]->id << "] " << users[i]->fname << " " << users[i]->lname << " <" << 
					users[i]->email_handle << "@jantofix.lol>" << std::endl;
				return ;
			}
			i++;
		}
		throw srv_exception("510 No such user here");
	} else if (splcmd[1] == "id") {
		int8_t id = 0;
		if (splcmd[2] == "-s"){
			id = std::stoi(splcmd[3]);
			std::cout << "250 " << "EXIST " << users[id]->id << std::endl;
		} else  {
			id = std::stoi(splcmd[2]);
			std::cout << "250 " << users[id]->fname << " " << users[id]->lname << " <" << 
				users[id]->email_handle << "@jantofix.lol>" << std::endl;;
		}
	} else {
		throw srv_exception("555 Bad syntax");
	}
}

User *find_mail(std::string handle){
	uint16_t i = 0;
	while (i < users_c){
		if ((users[i])->email_handle + "@jantofix.lol" == handle){
			return users[i];
		}
		i++;
	}
	return NULL;
}


void send_mail(std::vector<std::string> splcmd){
	if (splcmd.size() != 3){
		throw srv_exception("555 Bad syntax");
	}
	if (find_mail(splcmd[2]) != NULL){
		current_mail.sender = splcmd[2];
		throw srv_exception("250 Ok");
	} else {
		throw srv_exception("510 No such user here");
	}
}

void rcpt_mail(std::vector<std::string> splcmd){
	if (splcmd.size() != 3){
		throw srv_exception("555 Bad syntax");
	}
	if (find_mail(splcmd[2]) != NULL){
		current_mail.receiver = splcmd[2];
		throw srv_exception("250 Ok");
	}
	throw srv_exception("510 No such user here");
}

void mail_data(){
	char buffer[2048];
	if (current_mail.sender.empty() == false && current_mail.receiver.empty() == false){
		std::cout << "354 Continue" << std::endl;
		int stat = read(0, buffer, current_mail.dsize + 1);
		buffer[stat] = '\x00';
		User *receiver = find_mail(current_mail.receiver);
		if (receiver == NULL){
			throw srv_exception("510 No such user here");
		}
		memcpy(current_mail.data, buffer, current_mail.dsize + 1);
		current_mail.sent = true;
		receiver->inbox.push_back(current_mail);
		if (*buffer != '\x00'){
			throw srv_exception("354 Ok");
		} else {
			throw srv_exception("360 Data is empty");
		}
	} else {
		throw srv_exception("360 No receiver or sender");
	}
}

void clean_mail(){
	try {
		if (current_mail.dsize != 1024)
			throw (srv_exception("Tampering with emails detected"));
		bzero(current_mail.data, 1024);
		current_mail.sender = std::string();
		current_mail.receiver = std::string();
		current_mail.sent = false;
	} catch(...) {
		current_mail.dsize = 1024;
	}
}
 
int main(){
	std::cout << "220 jantofix.lol SMTP jantofix pseudo mail\n";
	while (1){
		try {
			for (std::string user_cmd; std::getline(std::cin, user_cmd);){
				std::vector<std::string> splcmd = split_cmd(user_cmd, ' ');
				if (splcmd.size() < 1){
					throw srv_exception("502 Empty request");
					break;
				} else if (splcmd.front() == "HELO" || splcmd.front() == "EHLO") {
					throw srv_exception("250 Ok");
				} else if (splcmd.front() == "NOOP"){
					throw srv_exception("250 Im okey :)");
				} else if (splcmd.front() == "QUIT"){
					std::cout << "221 That's about it, cya" << std::endl;
					std::exit(EXIT_SUCCESS);
				} else if (splcmd.front() == "AUTH"){
					create_user(splcmd);
				} else if (splcmd.front() == "RSET"){
					clean_mail();
				} else if (splcmd.front() == "VRFY"){
					verify_user(splcmd);
				} else if (splcmd.front() == "MAIL" && splcmd[1] == "FROM"){
					send_mail(splcmd);
				} else if (splcmd.front() == "RCPT" && splcmd[1] == "TO"){
					rcpt_mail(splcmd);
				} else if (splcmd.front() == "DATA"){
					mail_data();
				} else {
					throw srv_exception("502 Command Not Implemented");
				}
			} 
		} catch (srv_exception &exp){
			std::cout << exp.what() << std::endl;
		}
	}
}
