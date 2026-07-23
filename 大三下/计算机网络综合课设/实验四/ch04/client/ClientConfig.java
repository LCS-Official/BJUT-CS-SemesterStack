package com.cncd.ch04.client;

import java.io.*;
import java.util.Properties;

public class ClientConfig {
    private static final String CONFIG_FILE = System.getProperty("user.home")
            + System.getProperty("file.separator") + ".mihalychat"
            + System.getProperty("file.separator") + "client.properties";

    private static Properties props = new Properties();

    static {
        load();
    }

    public static void load() {
        File file = new File(CONFIG_FILE);
        if(file.exists()) {
            try(FileInputStream fis = new FileInputStream(file)) {
                props.load(fis);
            } catch(IOException e) {
                e.printStackTrace();
            }
        }
    }

    public static void save() {
        File dir = new File(CONFIG_FILE).getParentFile();
        if(!dir.exists()) dir.mkdirs();
        try(FileOutputStream fos = new FileOutputStream(CONFIG_FILE)) {
            props.store(fos, "Chat Client Configuration");
        } catch(IOException e) {
            e.printStackTrace();
        }
    }

    public static String get(String key, String defaultValue) {
        return props.getProperty(key, defaultValue);
    }

    public static void set(String key, String value) {
        props.setProperty(key, value);
        save();
    }

    public static int getInt(String key, int defaultValue) {
        try {
            return Integer.parseInt(get(key, String.valueOf(defaultValue)));
        } catch(NumberFormatException e) {
            return defaultValue;
        }
    }
}