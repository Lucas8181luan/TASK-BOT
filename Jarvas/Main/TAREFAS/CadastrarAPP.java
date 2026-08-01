package TAREFAS;
import java.awt.AWTException;
import java.awt.Robot;
import java.awt.event.KeyEvent;

public class CadastrarAPP {
    
    private static Robot robot;
    // CHROME
    // F10
    static {
        try {
            robot = new Robot();
        } catch (AWTException e) {
                System.err.println("Erro ao inicializar o Robot: " + e.getMessage());
        }
    }
    
    public static void executarCadastrarAPP() {
        int tempo = 2000; // 2 segundos em milissegundos
        
        for (int vezes = 0; vezes < 105; vezes++) {
            /** Função principal para redefinir senha */
            
            // Apps key (equivale ao menu de contexto/right click)
            pressKey(KeyEvent.VK_CONTEXT_MENU);
            timeSleep(2000);
            
            for (int i = 0; i < 3; i++) {
                pressKey(KeyEvent.VK_DOWN);
            }
            timeSleep(2000);
            
            for (int i = 0; i < 3; i++) {
                pressKey(KeyEvent.VK_RIGHT);
            }
            timeSleep(1000);
            
            pressKey(KeyEvent.VK_ENTER);
            timeSleep(1000);
            
            pressKey(KeyEvent.VK_ENTER);
            timeSleep(1000); 

            pressKey(KeyEvent.VK_RIGHT);
            timeSleep(1000);

            
            pressKey(KeyEvent.VK_ENTER);
            timeSleep(1000);
            
            pressKey(KeyEvent.VK_SPACE);
            timeSleep(1000);
            
            hotkey(KeyEvent.VK_ALT, KeyEvent.VK_TAB);
            timeSleep(tempo);
            
            hotkey(KeyEvent.VK_CONTROL, KeyEvent.VK_V);
            timeSleep(tempo);
            
            pressKey(KeyEvent.VK_DOWN);
            timeSleep(tempo);
            
            hotkey(KeyEvent.VK_ALT, KeyEvent.VK_TAB);
            timeSleep(tempo);
            
            pressKey(KeyEvent.VK_DOWN);
            timeSleep(tempo);
        }
    }
    
    // Métodos auxiliares
    private static void timeSleep(int milliseconds) {
        try {
            Thread.sleep(milliseconds);
        } catch (InterruptedException e) {
                System.err.println("Thread interrompida: " + e.getMessage());
        }
    }
    
    private static void pressKey(int keyCode) {
        robot.keyPress(keyCode);
        robot.keyRelease(keyCode);
    }
    
    private static void hotkey(int key1, int key2) {
        robot.keyPress(key1);
        robot.keyPress(key2);
        robot.keyRelease(key2);
        robot.keyRelease(key1);
    }
    
    // Executar apenas se chamado diretamente
    public static void main(String[] args) {
        try {
            System.out.println("Iniciando em 5 segundos...");
            Thread.sleep(5000);
            executarCadastrarAPP();
        } catch (InterruptedException e) {
                System.err.println("Thread interrompida: " + e.getMessage());
        }
    }
}