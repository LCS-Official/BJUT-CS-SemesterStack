package com.cncd.ch04.server;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Date;
import java.util.List;

class ServerChatLog {
    private static final long MAX_BYTES = 1024L * 1024L * 1024L;
    private static final Path DIR = Paths.get(System.getProperty("chat.history.dir", "history"));
    private static final SimpleDateFormat TS = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");

    static synchronized void chat(String target, String sender, String message) {
        append(fileName(target), "[" + TS.format(new Date()) + "] " + sender + ": " + message + "\n");
    }

    static synchronized void attachment(String target, String sender, String type, String fileName) {
        append(fileName(target), "[" + TS.format(new Date()) + "] " + sender + " sent " + type + ": " + fileName + "\n");
    }

    private static void append(String file, String line) {
        try {
            Files.createDirectories(DIR);
            pruneIfNeeded();
            Files.write(DIR.resolve(file), line.getBytes(StandardCharsets.UTF_8),
                    StandardOpenOption.CREATE, StandardOpenOption.APPEND);
            pruneIfNeeded();
        } catch(IOException e) {
            System.out.println("ServerChatLog: " + e.getMessage());
        }
    }

    private static String fileName(String target) {
        String safe = target == null || target.trim().length() == 0 ? "unknown" : target.trim();
        safe = safe.replaceAll("[\\\\/:*?\"<>|\\s]+", "_");
        if(safe.length() > 80) safe = safe.substring(0, 80);
        return safe + ".log";
    }

    private static void pruneIfNeeded() throws IOException {
        if(!Files.exists(DIR)) return;
        long total = 0;
        List<Path> files = new ArrayList<Path>();
        try(DirectoryStream<Path> stream = Files.newDirectoryStream(DIR, "*.log")) {
            for(Path file : stream) {
                files.add(file);
                total += Files.size(file);
            }
        }
        if(total <= MAX_BYTES) return;
        files.sort(Comparator.comparingLong(ServerChatLog::lastModified));
        for(Path file : files) {
            if(total <= MAX_BYTES * 9 / 10) break;
            long size = Files.size(file);
            Files.deleteIfExists(file);
            total -= size;
        }
    }

    private static long lastModified(Path file) {
        try {
            return Files.getLastModifiedTime(file).toMillis();
        } catch(IOException e) {
            return 0;
        }
    }
}
