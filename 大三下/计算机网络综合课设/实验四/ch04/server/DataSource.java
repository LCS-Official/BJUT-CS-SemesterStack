package com.cncd.ch04.server;
public interface DataSource {
    public boolean verifyUser(String user, String pass);
    public boolean addUser(String user, String pass);
    public boolean removeUser(String user, String pass);
    public boolean addInfo(String user, String field, String info);
    public boolean removeInfo(String user, String field, String info);
    public String[] getAllUserInfo(String user);
    public String[] getUserList();
}
